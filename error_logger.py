import logging
import traceback
from datetime import datetime
from flask import request
import os

# Configure error logging
def setup_error_logging(app):
    if not app.debug:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Configure file logging
        file_handler = logging.FileHandler('logs/forum_errors.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Forum startup')

# Enhanced error handler that logs detailed information
def log_error(error, app):
    """Log detailed error information"""
    error_info = {
        'timestamp': datetime.utcnow().isoformat(),
        'error_type': type(error).__name__,
        'error_message': str(error),
        'traceback': traceback.format_exc(),
        'request_method': request.method if request else 'N/A',
        'request_url': request.url if request else 'N/A',
        'user_agent': request.headers.get('User-Agent', 'N/A') if request else 'N/A',
        'remote_addr': request.remote_addr if request else 'N/A'
    }
    
    # Log to file
    app.logger.error(f"Forum Error: {error_info}")
    
    # Also save to a separate error file for easy access
    with open('logs/latest_error.txt', 'w') as f:
        f.write(f"Error occurred at: {error_info['timestamp']}\n")
        f.write(f"Type: {error_info['error_type']}\n")
        f.write(f"Message: {error_info['error_message']}\n")
        f.write(f"URL: {error_info['request_url']}\n")
        f.write(f"Method: {error_info['request_method']}\n")
        f.write(f"IP: {error_info['remote_addr']}\n")
        f.write(f"User Agent: {error_info['user_agent']}\n")
        f.write("\n--- Full Traceback ---\n")
        f.write(error_info['traceback'])
    
    return error_info
