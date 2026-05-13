"""
Bulk Operation Decorators

Flask decorators for bulk operations.
"""

from functools import wraps
from flask import request, jsonify, g
from typing import Dict, List, Any, Optional, Callable
import logging

from .bulk_manager import BulkOperationManager, BulkOperationConfig, BulkOperationType

logger = logging.getLogger(__name__)

def bulk_operation(resource_type: str, operation_type: BulkOperationType,
                 batch_size: int = 100, max_workers: int = 4,
                 timeout: int = 300, continue_on_error: bool = True,
                 validate_before_execute: bool = True):
    """Decorator for bulk operations"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get bulk operation manager
                bulk_manager = g.get('bulk_manager')
                if not bulk_manager:
                    bulk_manager = BulkOperationManager()
                    g.bulk_manager = bulk_manager
                
                # Parse request data
                data = request.get_json()
                if not data:
                    return jsonify({
                        'success': False,
                        'error': 'Request body is required'
                    }), 400
                
                # Extract items for bulk operation
                items = data.get('items', [])
                if not items:
                    return jsonify({
                        'success': False,
                        'error': 'No items provided for bulk operation'
                    }), 400
                
                # Create operation configuration
                config = BulkOperationConfig(
                    operation_type=operation_type,
                    resource_type=resource_type,
                    batch_size=batch_size,
                    max_workers=max_workers,
                    timeout=timeout,
                    continue_on_error=continue_on_error,
                    validate_before_execute=validate_before_execute,
                    generate_report=True
                )
                
                # Create and execute operation
                operation_id = bulk_manager.create_operation(config, items)
                
                # Execute operation asynchronously or synchronously
                async_execution = data.get('async', False)
                
                if async_execution:
                    # Return operation ID for async execution
                    # In production, this would use a proper async task queue
                    result = bulk_manager.execute_operation(operation_id)
                    return jsonify({
                        'success': True,
                        'data': {
                            'operation_id': operation_id,
                            'status': 'completed',
                            'result': result.__dict__
                        }
                    })
                else:
                    # Execute synchronously
                    result = bulk_manager.execute_operation(operation_id)
                    
                    return jsonify({
                        'success': True,
                        'data': {
                            'operation_id': operation_id,
                            'result': result.__dict__
                        }
                    })
            
            except Exception as e:
                logger.error(f"Error in bulk operation: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        return decorated_function
    return decorator

def bulk_create(resource_type: str, **kwargs):
    """Decorator for bulk create operations"""
    return bulk_operation(resource_type, BulkOperationType.CREATE, **kwargs)

def bulk_update(resource_type: str, **kwargs):
    """Decorator for bulk update operations"""
    return bulk_operation(resource_type, BulkOperationType.UPDATE, **kwargs)

def bulk_delete(resource_type: str, **kwargs):
    """Decorator for bulk delete operations"""
    return bulk_operation(resource_type, BulkOperationType.DELETE, **kwargs)

def bulk_import(resource_type: str, **kwargs):
    """Decorator for bulk import operations"""
    return bulk_operation(resource_type, BulkOperationType.IMPORT, **kwargs)

def bulk_export(resource_type: str, **kwargs):
    """Decorator for bulk export operations"""
    return bulk_operation(resource_type, BulkOperationType.EXPORT, **kwargs)

def bulk_upsert(resource_type: str, **kwargs):
    """Decorator for bulk upsert operations"""
    return bulk_operation(resource_type, BulkOperationType.UPSERT, **kwargs)

def file_upload_bulk_operation(resource_type: str, operation_type: BulkOperationType,
                             supported_formats: List[str] = None,
                             max_file_size: int = 10 * 1024 * 1024,  # 10MB
                             **kwargs):
    """Decorator for file-based bulk operations"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Check if file is provided
                if 'file' not in request.files:
                    return jsonify({
                        'success': False,
                        'error': 'No file provided'
                    }), 400
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({
                        'success': False,
                        'error': 'No file selected'
                    }), 400
                
                # Check file size
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Seek back to beginning
                
                if file_size > max_file_size:
                    return jsonify({
                        'success': False,
                        'error': f'File size exceeds maximum allowed size ({max_file_size} bytes)'
                    }), 400
                
                # Check file format
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                if supported_formats and file_extension not in supported_formats:
                    return jsonify({
                        'success': False,
                        'error': f'Unsupported file format. Supported formats: {", ".join(supported_formats)}'
                    }), 400
                
                # Read file content
                if file_extension in ['csv', 'json']:
                    content = file.read().decode('utf-8')
                else:
                    content = file.read()
                
                # Get bulk operation manager
                bulk_manager = g.get('bulk_manager')
                if not bulk_manager:
                    bulk_manager = BulkOperationManager()
                    g.bulk_manager = bulk_manager
                
                # Parse file content based on format
                from .bulk_processor import BulkDataProcessor
                processor = BulkDataProcessor()
                
                try:
                    data = processor.process_file(content, file_extension, resource_type)
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': f'Error parsing file: {str(e)}'
                    }), 400
                
                # Create operation configuration
                config = BulkOperationConfig(
                    operation_type=operation_type,
                    resource_type=resource_type,
                    batch_size=kwargs.get('batch_size', 100),
                    max_workers=kwargs.get('max_workers', 4),
                    timeout=kwargs.get('timeout', 300),
                    continue_on_error=kwargs.get('continue_on_error', True),
                    validate_before_execute=kwargs.get('validate_before_execute', True),
                    generate_report=True
                )
                
                # Create and execute operation
                operation_id = bulk_manager.create_operation(config, data)
                result = bulk_manager.execute_operation(operation_id)
                
                return jsonify({
                    'success': True,
                    'data': {
                        'operation_id': operation_id,
                        'file_name': file.filename,
                        'file_size': file_size,
                        'file_format': file_extension,
                        'items_processed': len(data),
                        'result': result.__dict__
                    }
                })
            
            except Exception as e:
                logger.error(f"Error in file-based bulk operation: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        return decorated_function
    return decorator

def bulk_operation_with_validation(resource_type: str, operation_type: BulkOperationType,
                                 validator_class=None, **kwargs):
    """Decorator for bulk operations with validation"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get data
                data = request.get_json()
                if not data:
                    return jsonify({
                        'success': False,
                        'error': 'Request body is required'
                    }), 400
                
                items = data.get('items', [])
                if not items:
                    return jsonify({
                        'success': False,
                        'error': 'No items provided for bulk operation'
                    }), 400
                
                # Validate data if validator is provided
                if validator_class:
                    from .bulk_validators import get_validator
                    validator = get_validator(resource_type) if not validator_class else validator_class()
                    
                    validation_result = validator.validate(items)
                    if not validation_result['valid']:
                        return jsonify({
                            'success': False,
                            'error': 'Validation failed',
                            'validation_errors': validation_result['errors']
                        }), 400
                    
                    # Add warnings to response
                    if validation_result['warnings']:
                        g.validation_warnings = validation_result['warnings']
                
                # Proceed with bulk operation
                return bulk_operation(resource_type, operation_type, **kwargs)(f)(*args, **kwargs)
            
            except Exception as e:
                logger.error(f"Error in validated bulk operation: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        return decorated_function
    return decorator

def bulk_operation_progress(operation_id_param: str = 'operation_id'):
    """Decorator for bulk operation progress tracking"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get operation ID from request
                operation_id = request.args.get(operation_id_param)
                if not operation_id:
                    return jsonify({
                        'success': False,
                        'error': f'Operation ID parameter "{operation_id_param}" is required'
                    }), 400
                
                # Get bulk operation manager
                bulk_manager = g.get('bulk_manager')
                if not bulk_manager:
                    bulk_manager = BulkOperationManager()
                    g.bulk_manager = bulk_manager
                
                # Get operation
                operation = bulk_manager.get_operation(operation_id)
                if not operation:
                    return jsonify({
                        'success': False,
                        'error': 'Operation not found'
                    }), 404
                
                # Return operation progress
                return jsonify({
                    'success': True,
                    'data': {
                        'operation_id': operation_id,
                        'status': operation.status.value,
                        'progress': {
                            'total_items': operation.result.total_items,
                            'processed_items': operation.result.processed_items,
                            'successful_items': operation.result.successful_items,
                            'failed_items': operation.result.failed_items,
                            'progress_percentage': operation.result.get_progress_percentage(),
                            'success_rate': operation.result.get_success_rate()
                        },
                        'timestamps': {
                            'created_at': operation.created_at.isoformat(),
                            'started_at': operation.started_at.isoformat() if operation.started_at else None,
                            'completed_at': operation.completed_at.isoformat() if operation.completed_at else None
                        },
                        'errors': operation.result.errors[-10:],  # Last 10 errors
                        'warnings': operation.result.warnings[-10:]  # Last 10 warnings
                    }
                })
            
            except Exception as e:
                logger.error(f"Error getting operation progress: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        return decorated_function
    return decorator

def bulk_operation_cancel():
    """Decorator for cancelling bulk operations"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get operation ID from request
                operation_id = request.args.get('operation_id')
                if not operation_id:
                    return jsonify({
                        'success': False,
                        'error': 'Operation ID parameter is required'
                    }), 400
                
                # Get bulk operation manager
                bulk_manager = g.get('bulk_manager')
                if not bulk_manager:
                    bulk_manager = BulkOperationManager()
                    g.bulk_manager = bulk_manager
                
                # Cancel operation
                success = bulk_manager.cancel_operation(operation_id)
                
                if success:
                    return jsonify({
                        'success': True,
                        'data': {
                            'operation_id': operation_id,
                            'status': 'cancelled',
                            'message': 'Operation cancelled successfully'
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to cancel operation or operation not found'
                    }), 400
            
            except Exception as e:
                logger.error(f"Error cancelling operation: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        return decorated_function
    return decorator

def bulk_operation_stats():
    """Decorator for bulk operation statistics"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get bulk operation manager
                bulk_manager = g.get('bulk_manager')
                if not bulk_manager:
                    bulk_manager = BulkOperationManager()
                    g.bulk_manager = bulk_manager
                
                # Get statistics
                stats = bulk_manager.get_stats()
                
                return jsonify({
                    'success': True,
                    'data': stats
                })
            
            except Exception as e:
                logger.error(f"Error getting bulk operation stats: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        return decorated_function
    return decorator

# Middleware for bulk operations
class BulkOperationMiddleware:
    """Middleware for bulk operations"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app"""
        app.config.setdefault('BULK_MAX_CONCURRENT_OPERATIONS', 5)
        app.config.setdefault('BULK_DEFAULT_BATCH_SIZE', 100)
        app.config.setdefault('BULK_MAX_FILE_SIZE', 10 * 1024 * 1024)  # 10MB
        app.config.setdefault('BULK_OPERATION_TIMEOUT', 300)  # 5 minutes
        
        # Add template context processor
        @app.context_processor
        def inject_bulk_context():
            """Inject bulk operation context into templates"""
            return {
                'bulk_config': {
                    'max_concurrent_operations': app.config['BULK_MAX_CONCURRENT_OPERATIONS'],
                    'default_batch_size': app.config['BULK_DEFAULT_BATCH_SIZE'],
                    'max_file_size': app.config['BULK_MAX_FILE_SIZE'],
                    'operation_timeout': app.config['BULK_OPERATION_TIMEOUT']
                }
            }
        
        # Register error handlers
        @app.errorhandler(413)
        def handle_file_too_large(error):
            """Handle file too large error"""
            return jsonify({
                'success': False,
                'error': 'File too large',
                'message': f'File size exceeds maximum allowed size ({app.config["BULK_MAX_FILE_SIZE"]} bytes)'
            }), 413

# Convenience decorators for common operations
def posts_bulk_create(**kwargs):
    """Bulk create posts"""
    return bulk_create('posts', **kwargs)

def posts_bulk_update(**kwargs):
    """Bulk update posts"""
    return bulk_update('posts', **kwargs)

def posts_bulk_delete(**kwargs):
    """Bulk delete posts"""
    return bulk_delete('posts', **kwargs)

def posts_bulk_import(**kwargs):
    """Bulk import posts"""
    return bulk_import('posts', supported_formats=['csv', 'json'], **kwargs)

def posts_bulk_export(**kwargs):
    """Bulk export posts"""
    return bulk_export('posts', **kwargs)

def users_bulk_create(**kwargs):
    """Bulk create users"""
    return bulk_create('users', **kwargs)

def users_bulk_update(**kwargs):
    """Bulk update users"""
    return bulk_update('users', **kwargs)

def users_bulk_delete(**kwargs):
    """Bulk delete users"""
    return bulk_delete('users', **kwargs)

def users_bulk_import(**kwargs):
    """Bulk import users"""
    return bulk_import('users', supported_formats=['csv', 'json'], **kwargs)

def users_bulk_export(**kwargs):
    """Bulk export users"""
    return bulk_export('users', **kwargs)

def comments_bulk_create(**kwargs):
    """Bulk create comments"""
    return bulk_create('comments', **kwargs)

def comments_bulk_update(**kwargs):
    """Bulk update comments"""
    return bulk_update('comments', **kwargs)

def comments_bulk_delete(**kwargs):
    """Bulk delete comments"""
    return bulk_delete('comments', **kwargs)

def comments_bulk_import(**kwargs):
    """Bulk import comments"""
    return bulk_import('comments', supported_formats=['csv', 'json'], **kwargs)

def comments_bulk_export(**kwargs):
    """Bulk export comments"""
    return bulk_export('comments', **kwargs)
