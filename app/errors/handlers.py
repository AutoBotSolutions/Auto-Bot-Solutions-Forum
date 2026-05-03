from flask import render_template, request
from app import db
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from error_logger import log_error

def page_not_found(e):
    # Log the 404 error
    if hasattr(request, 'url'):
        error_info = {
            'timestamp': str(datetime.utcnow()),
            'error_type': '404 Not Found',
            'error_message': f'Page not found: {request.url}',
            'request_method': request.method,
            'request_url': request.url,
            'remote_addr': request.remote_addr
        }
        print(f"404 Error: {error_info}")
    
    return render_template('errors/404.html'), 404

def internal_server_error(e):
    db.session.rollback()
    
    # Log the 500 error with full details
    try:
        from flask import current_app
        log_error(e, current_app)
    except Exception as log_error:
        print(f"Failed to log error: {log_error}")
        print(f"Original error: {e}")
    
    return render_template('errors/500.html'), 500
