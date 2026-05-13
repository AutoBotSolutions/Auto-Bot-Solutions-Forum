"""
Automatic Error Monitoring System
Provides real-time error detection and reporting for the Auto Bot Solutions Forum
"""

import logging
import traceback
import json
from datetime import datetime
from flask import request, g, current_app
from functools import wraps

# Configure error monitoring logger
error_logger = logging.getLogger('error_monitor')
error_logger.setLevel(logging.INFO)

# Create file handler for error logs
error_handler = logging.FileHandler('logs/error_monitor.log')
error_handler.setLevel(logging.INFO)
error_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
error_handler.setFormatter(error_formatter)
error_logger.addHandler(error_handler)

# In-memory error storage for recent errors
recent_errors = []
MAX_RECENT_ERRORS = 50

class ErrorMonitor:
    """Automatic error monitoring and reporting system"""
    
    @staticmethod
    def log_error(error, route=None, user_id=None):
        """Log an error with detailed information"""
        error_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'route': route or request.endpoint if request else 'unknown',
            'url': request.url if request else 'unknown',
            'method': request.method if request else 'unknown',
            'user_id': user_id or (g.user.id if hasattr(g, 'user') and g.user else None),
            'user_agent': request.headers.get('User-Agent', 'unknown') if request else 'unknown',
            'ip_address': request.remote_addr if request else 'unknown',
            'traceback': traceback.format_exc(),
            'form_data': dict(request.form) if request and request.form else {},
            'query_params': dict(request.args) if request and request.args else {}
        }
        
        # Add to recent errors
        recent_errors.append(error_info)
        if len(recent_errors) > MAX_RECENT_ERRORS:
            recent_errors.pop(0)
        
        # Log the error
        error_logger.error(f"Error in {error_info['route']}: {error_info['error_message']}")
        error_logger.error(f"Full error info: {json.dumps(error_info, indent=2, default=str)}")
        
        return error_info
    
    @staticmethod
    def get_recent_errors(limit=20):
        """Get recent errors"""
        return recent_errors[-limit:] if recent_errors else []
    
    @staticmethod
    def get_error_count():
        """Get total error count"""
        return len(recent_errors)
    
    @staticmethod
    def clear_errors():
        """Clear all stored errors"""
        recent_errors.clear()

# Error monitoring middleware
def error_monitoring_middleware(app):
    """Middleware to automatically monitor and log errors"""
    
    # Store the original exception handler if it exists
    original_exception_handler = None
    if hasattr(app, 'error_handler_spec') and Exception in app.error_handler_spec.get(None, {}):
        original_exception_handler = app.error_handler_spec[None][Exception]
    
    # Use a non-intrusive approach - don't override the exception handler
    # Instead, use teardown_request to catch exceptions
    @app.teardown_appcontext
    def teardown_appcontext(exception):
        """Log exceptions after app context teardown"""
        if exception:
            user_id = None
            try:
                from flask_login import current_user
                if current_user and hasattr(current_user, 'id'):
                    user_id = current_user.id
            except:
                pass
            
            ErrorMonitor.log_error(
                exception,
                route=request.endpoint if request else None,
                user_id=user_id
            )
    
    @app.errorhandler(404)
    def handle_404(error):
        """Handle 404 errors and log them"""
        user_id = None
        try:
            from flask_login import current_user
            if current_user and hasattr(current_user, 'id'):
                user_id = current_user.id
        except:
            pass
        
        error_info = ErrorMonitor.log_error(
            error, 
            route=request.endpoint if request else None,
            user_id=user_id
        )
        
        # Let Flask handle the 404 normally
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.before_request
    def before_request():
        """Store request context for error monitoring"""
        g.request_start_time = datetime.utcnow()
        g.request_id = id(request)
    
    @app.teardown_request
    def teardown_request(exception):
        """Log any unhandled exceptions"""
        if exception:
            user_id = None
            try:
                from flask_login import current_user
                if current_user and hasattr(current_user, 'id'):
                    user_id = current_user.id
            except:
                pass
            
            ErrorMonitor.log_error(
                exception,
                route=request.endpoint if request else None,
                user_id=user_id
            )
    
    return app

# Decorator for monitoring specific routes
def monitor_errors(func):
    """Decorator to monitor errors in specific routes"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            user_id = None
            if hasattr(g, 'user') and g.user and hasattr(g.user, 'id'):
                user_id = g.user.id
            
            ErrorMonitor.log_error(
                e,
                route=func.__name__,
                user_id=user_id
            )
            raise
    return wrapper

# Error reporting API endpoints
def create_error_reporting_routes(app):
    """Create routes for error reporting and monitoring"""
    
    @app.route('/admin/errors')
    @monitor_errors
    def admin_errors():
        """Admin route to view recent errors"""
        from flask_login import login_required, current_user
        
        if not (current_user.is_authenticated and current_user.is_admin):
            return "Access denied", 403
        
        errors = ErrorMonitor.get_recent_errors()
        return {
            'error_count': ErrorMonitor.get_error_count(),
            'recent_errors': errors,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    @app.route('/admin/errors/clear')
    @monitor_errors
    def clear_errors():
        """Admin route to clear error logs"""
        from flask_login import login_required, current_user
        
        if not (current_user.is_authenticated and current_user.is_admin):
            return "Access denied", 403
        
        ErrorMonitor.clear_errors()
        return {'status': 'success', 'message': 'Error logs cleared'}
    
    @app.route('/admin/errors/stats')
    @monitor_errors
    def error_stats():
        """Admin route to get error statistics"""
        from flask_login import login_required, current_user
        
        if not (current_user.is_authenticated and current_user.is_admin):
            return "Access denied", 403
        
        errors = ErrorMonitor.get_recent_errors()
        
        # Calculate statistics
        error_types = {}
        routes = {}
        hourly_errors = {}
        
        for error in errors:
            # Count by error type
            error_type = error['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # Count by route
            route = error['route']
            routes[route] = routes.get(route, 0) + 1
            
            # Count by hour
            try:
                hour = datetime.fromisoformat(error['timestamp']).hour
                hourly_errors[hour] = hourly_errors.get(hour, 0) + 1
            except:
                pass
        
        return {
            'total_errors': len(errors),
            'error_types': error_types,
            'routes': routes,
            'hourly_errors': hourly_errors,
            'timestamp': datetime.utcnow().isoformat()
        }

# Automatic error testing function
def test_error_monitoring():
    """Test the error monitoring system"""
    try:
        # Simulate an error
        raise ValueError("This is a test error for monitoring")
    except Exception as e:
        return ErrorMonitor.log_error(e, route='test_monitoring')

# Error monitoring initialization
def init_error_monitoring(app):
    """Initialize error monitoring for the Flask app"""
    app = error_monitoring_middleware(app)
    create_error_reporting_routes(app)
    
    # Log initialization
    error_logger.info("Error monitoring system initialized")
    
    return app
