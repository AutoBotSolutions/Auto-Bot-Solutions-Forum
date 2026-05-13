"""
Bulk Operations API Routes

Flask routes for bulk operations management and execution.
"""

from flask import Blueprint, jsonify, request, g
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# This would be initialized in the main app
bulk_bp = Blueprint('bulk', __name__, url_prefix='/api/bulk')

def init_bulk_routes(bulk_handlers):
    """Initialize bulk routes with handlers"""
    
    @bulk_bp.route('/operations', methods=['GET'])
    def get_operations():
        """Get all bulk operations"""
        try:
            status = request.args.get('status')
            resource_type = request.args.get('resource_type')
            operation_type = request.args.get('operation_type')
            
            operations = []
            for operation_id, operation in bulk_handlers.bulk_manager.operations.items():
                # Apply filters
                if status and operation.status.value != status:
                    continue
                if resource_type and operation.resource_type != resource_type:
                    continue
                if operation_type and operation.config.operation_type.value != operation_type:
                    continue
                
                operation_data = {
                    'operation_id': operation.operation_id,
                    'operation_type': operation.config.operation_type.value,
                    'resource_type': operation.resource_type,
                    'status': operation.status.value,
                    'total_items': operation.result.total_items,
                    'processed_items': operation.result.processed_items,
                    'successful_items': operation.result.successful_items,
                    'failed_items': operation.result.failed_items,
                    'created_at': operation.created_at.isoformat(),
                    'started_at': operation.started_at.isoformat() if operation.started_at else None,
                    'completed_at': operation.completed_at.isoformat() if operation.completed_at else None,
                    'duration': operation.result.duration
                }
                operations.append(operation_data)
            
            return jsonify({
                'success': True,
                'data': {
                    'operations': operations,
                    'total': len(operations),
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error getting operations: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @bulk_bp.route('/operations/<operation_id>', methods=['GET'])
    def get_operation_details(operation_id: str):
        """Get details for specific operation"""
        try:
            operation = bulk_handlers.bulk_manager.get_operation(operation_id)
            
            if not operation:
                return jsonify({
                    'success': False,
                    'error': 'Operation not found',
                    'message': f'Operation {operation_id} does not exist'
                }), 404
            
            return jsonify({
                'success': True,
                'data': {
                    'operation': {
                        'operation_id': operation.operation_id,
                        'operation_type': operation.config.operation_type.value,
                        'resource_type': operation.resource_type,
                        'status': operation.status.value,
                        'config': {
                            'batch_size': operation.config.batch_size,
                            'max_workers': operation.config.max_workers,
                            'timeout': operation.config.timeout,
                            'continue_on_error': operation.config.continue_on_error,
                            'validate_before_execute': operation.config.validate_before_execute
                        },
                        'result': operation.result.__dict__,
                        'timestamps': {
                            'created_at': operation.created_at.isoformat(),
                            'started_at': operation.started_at.isoformat() if operation.started_at else None,
                            'completed_at': operation.completed_at.isoformat() if operation.completed_at else None
                        }
                    }
                }
            })
        except Exception as e:
            logger.error(f"Error getting operation details: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @bulk_bp.route('/operations/<operation_id>/cancel', methods=['POST'])
    def cancel_operation(operation_id: str):
        """Cancel a bulk operation"""
        try:
            success = bulk_handlers.bulk_manager.cancel_operation(operation_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'operation_id': operation_id,
                        'status': 'cancelled',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to cancel operation',
                    'message': f'Could not cancel operation {operation_id}'
                }), 400
        except Exception as e:
            logger.error(f"Error cancelling operation: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @bulk_bp.route('/operations/<operation_id>/progress', methods=['GET'])
    def get_operation_progress(operation_id: str):
        """Get operation progress"""
        try:
            operation = bulk_handlers.bulk_manager.get_operation(operation_id)
            
            if not operation:
                return jsonify({
                    'success': False,
                    'error': 'Operation not found',
                    'message': f'Operation {operation_id} does not exist'
                }), 404
            
            progress_data = {
                'operation_id': operation_id,
                'status': operation.status.value,
                'progress': {
                    'total_items': operation.result.total_items,
                    'processed_items': operation.result.processed_items,
                    'successful_items': operation.result.successful_items,
                    'failed_items': operation.result.failed_items,
                    'skipped_items': operation.result.skipped_items,
                    'progress_percentage': operation.result.get_progress_percentage(),
                    'success_rate': operation.result.get_success_rate()
                },
                'timestamps': {
                    'created_at': operation.created_at.isoformat(),
                    'started_at': operation.started_at.isoformat() if operation.started_at else None,
                    'completed_at': operation.completed_at.isoformat() if operation.completed_at else None
                },
                'errors': operation.result.errors[-5:],  # Last 5 errors
                'warnings': operation.result.warnings[-5:]  # Last 5 warnings
            }
            
            return jsonify({
                'success': True,
                'data': progress_data
            })
        except Exception as e:
            logger.error(f"Error getting operation progress: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @bulk_bp.route('/operations/<operation_id>/errors', methods=['GET'])
    def get_operation_errors(operation_id: str):
        """Get operation errors"""
        try:
            operation = bulk_handlers.bulk_manager.get_operation(operation_id)
            
            if not operation:
                return jsonify({
                    'success': False,
                    'error': 'Operation not found',
                    'message': f'Operation {operation_id} does not exist'
                }), 404
            
            limit = request.args.get('limit', 50, type=int)
            errors = operation.result.errors[-limit:] if limit > 0 else operation.result.errors
            
            return jsonify({
                'success': True,
                'data': {
                    'operation_id': operation_id,
                    'total_errors': len(operation.result.errors),
                    'errors': errors,
                    'limit': limit,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error getting operation errors: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @bulk_bp.route('/stats', methods=['GET'])
    def get_bulk_stats():
        """Get bulk operation statistics"""
        try:
            stats = bulk_handlers.bulk_manager.get_stats()
            
            return jsonify({
                'success': True,
                'data': stats
            })
        except Exception as e:
            logger.error(f"Error getting bulk stats: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @bulk_bp.route('/cleanup', methods=['POST'])
    def cleanup_operations():
        """Clean up old operations"""
        try:
            data = request.get_json() or {}
            max_age_hours = data.get('max_age_hours', 24)
            
            cleaned_count = bulk_handlers.bulk_manager.cleanup_old_operations(max_age_hours)
            
            return jsonify({
                'success': True,
                'data': {
                    'cleaned_operations': cleaned_count,
                    'max_age_hours': max_age_hours,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error cleaning up operations: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @bulk_bp.route('/upload/<resource_type>', methods=['POST'])
    def upload_bulk_file(resource_type: str):
        """Upload file for bulk operation"""
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
            
            # Check file size (10MB limit)
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > 10 * 1024 * 1024:
                return jsonify({
                    'success': False,
                    'error': 'File size exceeds maximum allowed size (10MB)'
                }), 400
            
            # Check file format
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            supported_formats = ['csv', 'json', 'xlsx', 'xls']
            
            if file_extension not in supported_formats:
                return jsonify({
                    'success': False,
                    'error': f'Unsupported file format. Supported formats: {", ".join(supported_formats)}'
                }), 400
            
            # Read file content
            if file_extension in ['csv', 'json']:
                content = file.read().decode('utf-8')
            else:
                content = file.read()
            
            # Parse file content
            from .bulk_processor import BulkDataProcessor
            processor = BulkDataProcessor()
            
            try:
                data = processor.process_file(content, file_extension, resource_type)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Error parsing file: {str(e)}'
                }), 400
            
            # Return parsed data for preview
            return jsonify({
                'success': True,
                'data': {
                    'file_name': file.filename,
                    'file_size': file_size,
                    'file_format': file_extension,
                    'resource_type': resource_type,
                    'items_count': len(data),
                    'sample_items': data[:5]  # First 5 items for preview
                }
            })
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @bulk_bp.route('/validate/<resource_type>', methods=['POST'])
    def validate_bulk_data(resource_type: str):
        """Validate bulk data"""
        try:
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
                    'error': 'No items provided for validation'
                }), 400
            
            # Get validator
            from .bulk_validators import get_validator
            validator = get_validator(resource_type)
            
            validation_result = validator.validate(items)
            
            return jsonify({
                'success': True,
                'data': validation_result
            })
        except Exception as e:
            logger.error(f"Error validating data: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @bulk_bp.route('/templates/<resource_type>', methods=['GET'])
    def get_bulk_templates(resource_type: str):
        """Get bulk operation templates"""
        try:
            templates = _get_resource_templates(resource_type)
            
            if not templates:
                return jsonify({
                    'success': False,
                    'error': 'No templates found',
                    'message': f'No templates available for resource type: {resource_type}'
                }), 404
            
            return jsonify({
                'success': True,
                'data': {
                    'resource_type': resource_type,
                    'templates': templates
                }
            })
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @bulk_bp.route('/export/<resource_type>', methods=['POST'])
    def export_bulk_data(resource_type: str):
        """Export bulk data"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Request body is required'
                }), 400
            
            export_format = data.get('format', 'json')
            filters = data.get('filters', {})
            
            # Get data to export (placeholder - would query database)
            export_data = _get_export_data(resource_type, filters)
            
            if not export_data:
                return jsonify({
                    'success': False,
                    'error': 'No data found for export'
                }), 404
            
            # Generate file content
            from .bulk_processor import BulkDataProcessor
            processor = BulkDataProcessor()
            
            try:
                file_content = processor.generate_file(export_data, export_format, resource_type)
                
                return jsonify({
                    'success': True,
                    'data': {
                        'resource_type': resource_type,
                        'format': export_format,
                        'items_count': len(export_data),
                        'file_content': file_content
                    }
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Error generating export file: {str(e)}'
                }), 400
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @bulk_bp.route('/config', methods=['GET'])
    def get_bulk_config():
        """Get bulk operation configuration"""
        try:
            config = {
                'bulk_operations': {
                    'max_concurrent_operations': 5,
                    'default_batch_size': 100,
                    'max_batch_size': 1000,
                    'default_timeout': 300,
                    'max_timeout': 3600
                },
                'file_processing': {
                    'supported_formats': ['csv', 'json', 'xlsx', 'xls'],
                    'max_file_size': 10485760,  # 10MB
                    'max_items_per_file': 10000
                },
                'validation': {
                    'validate_before_execute': True,
                    'continue_on_validation_error': False,
                    'max_validation_errors': 100
                },
                'processing': {
                    'default_max_workers': 4,
                    'max_max_workers': 10,
                    'retry_failed': True,
                    'max_retries': 3
                },
                'reporting': {
                    'generate_report': True,
                    'include_warnings': True,
                    'max_errors_in_report': 1000
                }
            }
            
            return jsonify({
                'success': True,
                'data': config
            })
        except Exception as e:
            logger.error(f"Error getting bulk config: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @bulk_bp.route('/health', methods=['GET'])
    def bulk_health():
        """Get bulk operations health status"""
        try:
            stats = bulk_handlers.bulk_manager.get_stats()
            bulk_stats = stats.get('stats', {})
            
            # Calculate health metrics
            active_operations = bulk_stats.get('active_operations', 0)
            queued_operations = bulk_stats.get('queued_operations', 0)
            total_operations = bulk_stats.get('total_operations', 0)
            failed_operations = bulk_stats.get('failed_operations', 0)
            avg_processing_time = bulk_stats.get('average_processing_time', 0)
            
            health_status = 'healthy'
            issues = []
            warnings = []
            
            # Check for issues
            if active_operations >= 5:
                health_status = 'warning'
                warnings.append(f"High number of active operations: {active_operations}")
            
            if failed_operations > total_operations * 0.1:  # More than 10% failed
                health_status = 'critical'
                issues.append(f"High failure rate: {failed_operations}/{total_operations}")
            
            if avg_processing_time > 300:  # More than 5 minutes
                health_status = 'warning'
                warnings.append(f"Slow processing time: {avg_processing_time:.2f}s")
            
            return jsonify({
                'success': True,
                'data': {
                    'health_status': health_status,
                    'metrics': {
                        'active_operations': active_operations,
                        'queued_operations': queued_operations,
                        'total_operations': total_operations,
                        'failed_operations': failed_operations,
                        'average_processing_time': avg_processing_time
                    },
                    'issues': issues,
                    'warnings': warnings,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error getting bulk health: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500

def _get_resource_templates(resource_type: str) -> Dict[str, Any]:
    """Get templates for resource type"""
    templates = {
        'posts': {
            'create': {
                'description': 'Create multiple posts',
                'required_fields': ['title', 'content'],
                'optional_fields': ['author_id', 'status', 'tags', 'category_id'],
                'example': {
                    'items': [
                        {
                            'title': 'Sample Post 1',
                            'content': 'This is the content of the first post',
                            'author_id': 1,
                            'status': 'published'
                        },
                        {
                            'title': 'Sample Post 2',
                            'content': 'This is the content of the second post',
                            'author_id': 2,
                            'status': 'draft'
                        }
                    ]
                }
            },
            'update': {
                'description': 'Update multiple posts',
                'required_fields': ['id'],
                'optional_fields': ['title', 'content', 'status', 'tags'],
                'example': {
                    'items': [
                        {
                            'id': 1,
                            'title': 'Updated Title',
                            'content': 'Updated content'
                        },
                        {
                            'id': 2,
                            'status': 'published'
                        }
                    ]
                }
            },
            'delete': {
                'description': 'Delete multiple posts',
                'required_fields': ['id'],
                'example': {
                    'items': [
                        {'id': 1},
                        {'id': 2}
                    ]
                }
            }
        },
        'users': {
            'create': {
                'description': 'Create multiple users',
                'required_fields': ['username', 'email'],
                'optional_fields': ['password', 'first_name', 'last_name', 'role'],
                'example': {
                    'items': [
                        {
                            'username': 'user1',
                            'email': 'user1@example.com',
                            'password': 'password123',
                            'role': 'user'
                        },
                        {
                            'username': 'user2',
                            'email': 'user2@example.com',
                            'password': 'password456',
                            'role': 'user'
                        }
                    ]
                }
            },
            'update': {
                'description': 'Update multiple users',
                'required_fields': ['id'],
                'optional_fields': ['username', 'email', 'role', 'is_active'],
                'example': {
                    'items': [
                        {
                            'id': 1,
                            'role': 'admin'
                        },
                        {
                            'id': 2,
                            'is_active': False
                        }
                    ]
                }
            }
        },
        'comments': {
            'create': {
                'description': 'Create multiple comments',
                'required_fields': ['content', 'post_id', 'author_id'],
                'optional_fields': ['parent_id', 'status'],
                'example': {
                    'items': [
                        {
                            'content': 'Great post!',
                            'post_id': 1,
                            'author_id': 1
                        },
                        {
                            'content': 'Thanks for sharing',
                            'post_id': 1,
                            'author_id': 2
                        }
                    ]
                }
            }
        }
    }
    
    return templates.get(resource_type, {})

def _get_export_data(resource_type: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get data for export (placeholder implementation)"""
    # This would query the database based on filters
    # For now, return sample data
    
    if resource_type == 'posts':
        return [
            {
                'id': 1,
                'title': 'Sample Post 1',
                'content': 'This is sample content',
                'author_id': 1,
                'status': 'published',
                'created_at': datetime.utcnow().isoformat()
            },
            {
                'id': 2,
                'title': 'Sample Post 2',
                'content': 'This is another sample',
                'author_id': 2,
                'status': 'draft',
                'created_at': datetime.utcnow().isoformat()
            }
        ]
    elif resource_type == 'users':
        return [
            {
                'id': 1,
                'username': 'user1',
                'email': 'user1@example.com',
                'role': 'user',
                'is_active': True,
                'created_at': datetime.utcnow().isoformat()
            },
            {
                'id': 2,
                'username': 'user2',
                'email': 'user2@example.com',
                'role': 'admin',
                'is_active': True,
                'created_at': datetime.utcnow().isoformat()
            }
        ]
    elif resource_type == 'comments':
        return [
            {
                'id': 1,
                'content': 'Sample comment',
                'post_id': 1,
                'author_id': 1,
                'status': 'approved',
                'created_at': datetime.utcnow().isoformat()
            },
            {
                'id': 2,
                'content': 'Another sample comment',
                'post_id': 1,
                'author_id': 2,
                'status': 'approved',
                'created_at': datetime.utcnow().isoformat()
            }
        ]
    
    return []
