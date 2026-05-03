"""
Comprehensive Error Handling and Reporting System
"""

import logging
import traceback
import sys
from datetime import datetime
from functools import wraps
from flask import request, jsonify, current_app
from flask_login import current_user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_errors.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ErrorReporter:
    """Comprehensive error reporting system"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info_messages = []
    
    def log_error(self, error, context=None, user_id=None):
        """Log an error with full context"""
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'ERROR',
            'message': str(error),
            'context': context or {},
            'user_id': user_id or (current_user.id if current_user.is_authenticated else None),
            'url': request.url if request else None,
            'method': request.method if request else None,
            'traceback': traceback.format_exc() if isinstance(error, Exception) else None
        }
        
        self.errors.append(error_data)
        logger.error(f"Error: {error_data}")
        
        return error_data
    
    def log_warning(self, warning, context=None, user_id=None):
        """Log a warning with context"""
        warning_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'WARNING',
            'message': str(warning),
            'context': context or {},
            'user_id': user_id or (current_user.id if current_user.is_authenticated else None),
            'url': request.url if request else None,
            'method': request.method if request else None
        }
        
        self.warnings.append(warning_data)
        logger.warning(f"Warning: {warning_data}")
        
        return warning_data
    
    def log_info(self, info, context=None, user_id=None):
        """Log informational message"""
        info_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'INFO',
            'message': str(info),
            'context': context or {},
            'user_id': user_id or (current_user.id if current_user.is_authenticated else None),
            'url': request.url if request else None,
            'method': request.method if request else None
        }
        
        self.info_messages.append(info_data)
        logger.info(f"Info: {info_data}")
        
        return info_data
    
    def get_error_report(self):
        """Get comprehensive error report"""
        return {
            'errors': self.errors[-10:],  # Last 10 errors
            'warnings': self.warnings[-10:],  # Last 10 warnings
            'info': self.info_messages[-5:],  # Last 5 info messages
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'generated_at': datetime.now().isoformat()
        }
    
    def clear_logs(self):
        """Clear all logs"""
        self.errors.clear()
        self.warnings.clear()
        self.info_messages.clear()

# Global error reporter instance
error_reporter = ErrorReporter()

def debug_route(func):
    """Decorator to debug route functions"""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        try:
            error_reporter.log_info(f"Route accessed: {request.url}", {
                'function': func.__name__,
                'args': args,
                'kwargs': kwargs
            })
            
            result = func(*args, **kwargs)
            
            if hasattr(result, 'status_code'):
                error_reporter.log_info(f"Route completed: {request.url}", {
                    'function': func.__name__,
                    'status_code': result.status_code
                })
            
            return result
            
        except Exception as e:
            error_reporter.log_error(e, {
                'function': func.__name__,
                'args': args,
                'kwargs': kwargs
            })
            raise
    
    return decorated_function

def validate_admin_access(func):
    """Decorator to validate admin access and log issues"""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        try:
            # Check if user is authenticated
            if not current_user.is_authenticated:
                error_reporter.log_warning("Unauthenticated access attempt", {
                    'function': func.__name__,
                    'url': request.url
                })
                return jsonify({'error': 'Authentication required'}), 401
            
            # Check if user is admin
            if not current_user.is_admin:
                error_reporter.log_warning("Non-admin access attempt", {
                    'function': func.__name__,
                    'user_id': current_user.id,
                    'url': request.url
                })
                return jsonify({'error': 'Admin access required'}), 403
            
            error_reporter.log_info(f"Admin access granted: {request.url}", {
                'function': func.__name__,
                'user_id': current_user.id
            })
            
            return func(*args, **kwargs)
            
        except Exception as e:
            error_reporter.log_error(e, {
                'function': func.__name__,
                'user_id': current_user.id if current_user.is_authenticated else None
            })
            raise
    
    return decorated_function

def check_template_rendering(template_name, context=None):
    """Check if template can be rendered successfully"""
    try:
        from flask import render_template
        result = render_template(template_name, **(context or {}))
        error_reporter.log_info(f"Template rendered successfully: {template_name}", {
            'template': template_name,
            'context_keys': list(context.keys()) if context else []
        })
        return True, result
    except Exception as e:
        error_reporter.log_error(f"Template rendering failed: {template_name}", {
            'template': template_name,
            'context_keys': list(context.keys()) if context else [],
            'error': str(e)
        })
        return False, str(e)

def check_route_exists(route_path):
    """Check if route exists and is accessible"""
    try:
        from flask import current_app
        adapter = current_app.url_map.bind_to_environ(request.environ)
        endpoint, values = adapter.match()
        error_reporter.log_info(f"Route found: {route_path}", {
            'endpoint': endpoint,
            'values': values
        })
        return True, endpoint, values
    except Exception as e:
        error_reporter.log_warning(f"Route not found: {route_path}", {
            'error': str(e)
        })
        return False, None, None

def check_database_connection():
    """Check database connection and user data"""
    try:
        from app import db
        from app.models import User
        
        users = User.query.all()
        error_reporter.log_info("Database connection successful", {
            'user_count': len(users)
        })
        
        # Check for admin user
        admin_user = User.query.filter_by(is_admin=True).first()
        if admin_user:
            error_reporter.log_info("Admin user found", {
                'admin_username': admin_user.username
            })
        else:
            error_reporter.log_warning("No admin user found")
        
        return True, len(users)
        
    except Exception as e:
        error_reporter.log_error("Database connection failed", {
            'error': str(e)
        })
        return False, 0

def get_system_health_check():
    """Comprehensive system health check"""
    health_report = {
        'timestamp': datetime.now().isoformat(),
        'status': 'unknown',
        'checks': {}
    }
    
    try:
        # Check app creation
        try:
            from app import create_app
            app = create_app()
            health_report['checks']['app_creation'] = {'status': 'ok', 'message': 'App created successfully'}
        except Exception as e:
            health_report['checks']['app_creation'] = {'status': 'error', 'message': str(e)}
        
        # Check blueprint registration
        try:
            from app.admin.routes import admin_bp
            if 'admin' in app.blueprints:
                health_report['checks']['blueprint'] = {'status': 'ok', 'message': 'Admin blueprint registered'}
            else:
                health_report['checks']['blueprint'] = {'status': 'error', 'message': 'Admin blueprint not registered'}
        except Exception as e:
            health_report['checks']['blueprint'] = {'status': 'error', 'message': str(e)}
        
        # Check route registration
        try:
            admin_routes = [rule for rule in app.url_map.iter_rules() if 'admin/users' in rule.rule]
            if admin_routes:
                health_report['checks']['routes'] = {'status': 'ok', 'message': f'Found {len(admin_routes)} admin routes'}
            else:
                health_report['checks']['routes'] = {'status': 'error', 'message': 'No admin routes found'}
        except Exception as e:
            health_report['checks']['routes'] = {'status': 'error', 'message': str(e)}
        
        # Check database
        db_ok, user_count = check_database_connection()
        health_report['checks']['database'] = {
            'status': 'ok' if db_ok else 'error',
            'message': f'{user_count} users found' if db_ok else 'Database connection failed'
        }
        
        # Check template
        template_ok, template_result = check_template_rendering('admin/users.html', users=[])
        health_report['checks']['template'] = {
            'status': 'ok' if template_ok else 'error',
            'message': 'Template renders successfully' if template_ok else f'Template error: {template_result}'
        }
        
        # Overall status
        all_ok = all(check['status'] == 'ok' for check in health_report['checks'].values())
        health_report['status'] = 'healthy' if all_ok else 'unhealthy'
        
    except Exception as e:
        error_reporter.log_error("Health check failed", {'error': str(e)})
        health_report['status'] = 'error'
        health_report['error'] = str(e)
    
    return health_report
