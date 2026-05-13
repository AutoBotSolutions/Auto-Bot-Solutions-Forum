"""
Bulk Operation Manager

Manages bulk operations for efficient batch processing.
"""

import uuid
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class BulkOperationType(Enum):
    """Bulk operation types"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    IMPORT = "import"
    EXPORT = "export"
    UPSERT = "upsert"

class BulkOperationStatus(Enum):
    """Bulk operation status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"

@dataclass
class BulkOperationConfig:
    """Configuration for bulk operations"""
    operation_type: BulkOperationType
    resource_type: str
    batch_size: int = 100
    max_workers: int = 4
    timeout: int = 300  # seconds
    retry_failed: bool = True
    max_retries: int = 3
    continue_on_error: bool = True
    validate_before_execute: bool = True
    generate_report: bool = True
    notify_on_completion: bool = False

@dataclass
class BulkOperationResult:
    """Result of a bulk operation"""
    operation_id: str
    operation_type: BulkOperationType
    resource_type: str
    status: BulkOperationStatus
    total_items: int
    processed_items: int
    successful_items: int
    failed_items: int
    skipped_items: int
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    report: Optional[Dict[str, Any]] = None
    
    def get_success_rate(self) -> float:
        """Get success rate percentage"""
        if self.processed_items == 0:
            return 0.0
        return (self.successful_items / self.processed_items) * 100
    
    def get_progress_percentage(self) -> float:
        """Get progress percentage"""
        if self.total_items == 0:
            return 100.0
        return (self.processed_items / self.total_items) * 100

class BulkOperation:
    """Represents a bulk operation"""
    
    def __init__(self, config: BulkOperationConfig, data: List[Dict[str, Any]] = None):
        self.operation_id = str(uuid.uuid4())
        self.config = config
        self.data = data or []
        self.status = BulkOperationStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.result = BulkOperationResult(
            operation_id=self.operation_id,
            operation_type=config.operation_type,
            resource_type=config.resource_type,
            status=BulkOperationStatus.PENDING,
            total_items=len(self.data),
            processed_items=0,
            successful_items=0,
            failed_items=0,
            skipped_items=0
        )
        self.progress_callback = None
        self.error_callback = None
        self.completion_callback = None
    
    def set_progress_callback(self, callback: Callable):
        """Set progress callback"""
        self.progress_callback = callback
    
    def set_error_callback(self, callback: Callable):
        """Set error callback"""
        self.error_callback = callback
    
    def set_completion_callback(self, callback: Callable):
        """Set completion callback"""
        self.completion_callback = callback
    
    def update_progress(self, processed: int, successful: int, failed: int, skipped: int = 0):
        """Update operation progress"""
        self.result.processed_items = processed
        self.result.successful_items = successful
        self.result.failed_items = failed
        self.result.skipped_items = skipped
        
        if self.progress_callback:
            self.progress_callback(self.result)
    
    def add_error(self, error: Dict[str, Any]):
        """Add error to result"""
        self.result.errors.append(error)
        
        if self.error_callback:
            self.error_callback(self.result, error)
    
    def add_warning(self, warning: Dict[str, Any]):
        """Add warning to result"""
        self.result.warnings.append(warning)
    
    def start(self):
        """Start the operation"""
        self.status = BulkOperationStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.result.status = BulkOperationStatus.RUNNING
        self.result.start_time = self.started_at
    
    def complete(self, status: BulkOperationStatus = BulkOperationStatus.COMPLETED):
        """Complete the operation"""
        self.status = status
        self.completed_at = datetime.utcnow()
        self.result.status = status
        self.result.end_time = self.completed_at
        
        if self.started_at:
            self.result.duration = (self.completed_at - self.started_at).total_seconds()
        
        if self.completion_callback:
            self.completion_callback(self.result)

class BulkOperationManager:
    """Manages bulk operations"""
    
    def __init__(self, max_concurrent_operations: int = 5):
        self.operations: Dict[str, BulkOperation] = {}
        self.max_concurrent_operations = max_concurrent_operations
        self.active_operations: Set[str] = set()
        self.operation_handlers: Dict[str, Dict[BulkOperationType, Callable]] = {}
        self.validators: Dict[str, Callable] = {}
        self.transformers: Dict[str, Callable] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_operations)
        self.stats = {
            'total_operations': 0,
            'completed_operations': 0,
            'failed_operations': 0,
            'total_items_processed': 0,
            'average_processing_time': 0.0
        }
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default operation handlers"""
        # Register default resource handlers
        self.register_handler('posts', BulkOperationType.CREATE, self._create_posts)
        self.register_handler('posts', BulkOperationType.UPDATE, self._update_posts)
        self.register_handler('posts', BulkOperationType.DELETE, self._delete_posts)
        self.register_handler('posts', BulkOperationType.IMPORT, self._import_posts)
        self.register_handler('posts', BulkOperationType.EXPORT, self._export_posts)
        
        self.register_handler('users', BulkOperationType.CREATE, self._create_users)
        self.register_handler('users', BulkOperationType.UPDATE, self._update_users)
        self.register_handler('users', BulkOperationType.DELETE, self._delete_users)
        self.register_handler('users', BulkOperationType.IMPORT, self._import_users)
        self.register_handler('users', BulkOperationType.EXPORT, self._export_users)
        
        self.register_handler('comments', BulkOperationType.CREATE, self._create_comments)
        self.register_handler('comments', BulkOperationType.UPDATE, self._update_comments)
        self.register_handler('comments', BulkOperationType.DELETE, self._delete_comments)
        self.register_handler('comments', BulkOperationType.IMPORT, self._import_comments)
        self.register_handler('comments', BulkOperationType.EXPORT, self._export_comments)
    
    def register_handler(self, resource_type: str, operation_type: BulkOperationType, 
                       handler: Callable):
        """Register operation handler"""
        if resource_type not in self.operation_handlers:
            self.operation_handlers[resource_type] = {}
        self.operation_handlers[resource_type][operation_type] = handler
    
    def register_validator(self, resource_type: str, validator: Callable):
        """Register data validator"""
        self.validators[resource_type] = validator
    
    def register_transformer(self, resource_type: str, transformer: Callable):
        """Register data transformer"""
        self.transformers[resource_type] = transformer
    
    def create_operation(self, config: BulkOperationConfig, 
                        data: List[Dict[str, Any]] = None) -> str:
        """Create a new bulk operation"""
        operation = BulkOperation(config, data)
        self.operations[operation.operation_id] = operation
        self.stats['total_operations'] += 1
        
        logger.info(f"Created bulk operation {operation.operation_id} for {config.resource_type}")
        return operation.operation_id
    
    def execute_operation(self, operation_id: str) -> BulkOperationResult:
        """Execute a bulk operation"""
        operation = self.operations.get(operation_id)
        if not operation:
            raise ValueError(f"Operation {operation_id} not found")
        
        if operation.status != BulkOperationStatus.PENDING:
            raise ValueError(f"Operation {operation_id} is not in pending status")
        
        # Check concurrent operation limit
        if len(self.active_operations) >= self.max_concurrent_operations:
            raise RuntimeError("Maximum concurrent operations reached")
        
        # Submit operation to executor
        future = self.executor.submit(self._execute_operation_sync, operation)
        self.active_operations.add(operation_id)
        
        # Wait for completion (in production, this would be async)
        try:
            result = future.result(timeout=operation.config.timeout)
            return result
        finally:
            self.active_operations.discard(operation_id)
    
    def _execute_operation_sync(self, operation: BulkOperation) -> BulkOperationResult:
        """Execute operation synchronously"""
        try:
            operation.start()
            
            # Validate data if required
            if operation.config.validate_before_execute:
                validation_result = self._validate_operation_data(operation)
                if not validation_result['valid']:
                    operation.add_error({
                        'type': 'validation_error',
                        'message': 'Data validation failed',
                        'errors': validation_result['errors']
                    })
                    operation.complete(BulkOperationStatus.FAILED)
                    return operation.result
            
            # Transform data if transformer exists
            if operation.resource_type in self.transformers:
                operation.data = self.transformers[operation.resource_type](operation.data)
            
            # Get operation handler
            handlers = self.operation_handlers.get(operation.resource_type, {})
            handler = handlers.get(operation.config.operation_type)
            
            if not handler:
                operation.add_error({
                    'type': 'handler_not_found',
                    'message': f"No handler for {operation.config.operation_type.value} on {operation.resource_type}"
                })
                operation.complete(BulkOperationStatus.FAILED)
                return operation.result
            
            # Execute operation
            handler(operation)
            
            # Determine final status
            if operation.result.failed_items > 0:
                if operation.result.successful_items > 0:
                    operation.complete(BulkOperationStatus.PARTIAL)
                else:
                    operation.complete(BulkOperationStatus.FAILED)
            else:
                operation.complete(BulkOperationStatus.COMPLETED)
            
            # Update stats
            self._update_stats(operation)
            
            return operation.result
        
        except Exception as e:
            logger.error(f"Error executing operation {operation.operation_id}: {e}")
            operation.add_error({
                'type': 'execution_error',
                'message': str(e)
            })
            operation.complete(BulkOperationStatus.FAILED)
            return operation.result
    
    def _validate_operation_data(self, operation: BulkOperation) -> Dict[str, Any]:
        """Validate operation data"""
        validator = self.validators.get(operation.resource_type)
        if not validator:
            return {'valid': True, 'errors': []}
        
        try:
            return validator(operation.data)
        except Exception as e:
            return {'valid': False, 'errors': [str(e)]}
    
    def _update_stats(self, operation: BulkOperation):
        """Update operation statistics"""
        if operation.result.status == BulkOperationStatus.COMPLETED:
            self.stats['completed_operations'] += 1
        elif operation.result.status == BulkOperationStatus.FAILED:
            self.stats['failed_operations'] += 1
        
        self.stats['total_items_processed'] += operation.result.processed_items
        
        # Update average processing time
        if operation.result.duration:
            total_time = self.stats['average_processing_time'] * (self.stats['completed_operations'] - 1)
            total_time += operation.result.duration
            self.stats['average_processing_time'] = total_time / self.stats['completed_operations']
    
    def get_operation(self, operation_id: str) -> Optional[BulkOperation]:
        """Get operation by ID"""
        return self.operations.get(operation_id)
    
    def get_operation_result(self, operation_id: str) -> Optional[BulkOperationResult]:
        """Get operation result by ID"""
        operation = self.get_operation(operation_id)
        return operation.result if operation else None
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel an operation"""
        operation = self.get_operation(operation_id)
        if not operation:
            return False
        
        if operation.status in [BulkOperationStatus.COMPLETED, BulkOperationStatus.FAILED, BulkOperationStatus.CANCELLED]:
            return False
        
        operation.status = BulkOperationStatus.CANCELLED
        operation.result.status = BulkOperationStatus.CANCELLED
        operation.complete(BulkOperationStatus.CANCELLED)
        
        self.active_operations.discard(operation_id)
        logger.info(f"Cancelled operation {operation_id}")
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bulk operation statistics"""
        return {
            'stats': self.stats.copy(),
            'active_operations': len(self.active_operations),
            'queued_operations': len(self.operations) - len(self.active_operations),
            'max_concurrent_operations': self.max_concurrent_operations
        }
    
    def cleanup_old_operations(self, max_age_hours: int = 24) -> int:
        """Clean up old operations"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        old_operations = []
        for operation_id, operation in self.operations.items():
            if operation.completed_at and operation.completed_at < cutoff_time:
                old_operations.append(operation_id)
        
        for operation_id in old_operations:
            del self.operations[operation_id]
        
        logger.info(f"Cleaned up {len(old_operations)} old operations")
        return len(old_operations)
    
    # Default operation handlers (placeholders - would be implemented with actual database operations)
    
    def _create_posts(self, operation: BulkOperation):
        """Create posts in bulk"""
        batch_size = operation.config.batch_size
        processed = 0
        successful = 0
        failed = 0
        
        for i in range(0, len(operation.data), batch_size):
            batch = operation.data[i:i + batch_size]
            
            for item in batch:
                try:
                    # Simulate post creation
                    # In production, this would use actual database operations
                    processed += 1
                    successful += 1
                    
                    # Update progress
                    operation.update_progress(processed, successful, failed)
                    
                except Exception as e:
                    failed += 1
                    operation.add_error({
                        'item_index': processed,
                        'error': str(e),
                        'data': item
                    })
                    processed += 1
                    
                    if not operation.config.continue_on_error:
                        raise
            
            # Small delay to simulate processing
            import time
            time.sleep(0.1)
    
    def _update_posts(self, operation: BulkOperation):
        """Update posts in bulk"""
        # Similar to create_posts but for updates
        self._create_posts(operation)  # Placeholder
    
    def _delete_posts(self, operation: BulkOperation):
        """Delete posts in bulk"""
        # Similar to create_posts but for deletions
        self._create_posts(operation)  # Placeholder
    
    def _import_posts(self, operation: BulkOperation):
        """Import posts in bulk"""
        # Similar to create_posts but for imports
        self._create_posts(operation)  # Placeholder
    
    def _export_posts(self, operation: BulkOperation):
        """Export posts in bulk"""
        # Export operation would query database and create export file
        operation.update_progress(len(operation.data), len(operation.data), 0)
    
    def _create_users(self, operation: BulkOperation):
        """Create users in bulk"""
        self._create_posts(operation)  # Placeholder
    
    def _update_users(self, operation: BulkOperation):
        """Update users in bulk"""
        self._create_posts(operation)  # Placeholder
    
    def _delete_users(self, operation: BulkOperation):
        """Delete users in bulk"""
        self._create_posts(operation)  # Placeholder
    
    def _import_users(self, operation: BulkOperation):
        """Import users in bulk"""
        self._create_posts(operation)  # Placeholder
    
    def _export_users(self, operation: BulkOperation):
        """Export users in bulk"""
        self._create_posts(operation)  # Placeholder
    
    def _create_comments(self, operation: BulkOperation):
        """Create comments in bulk"""
        self._create_posts(operation)  # Placeholder
    
    def _update_comments(self, operation: BulkOperation):
        """Update comments in bulk"""
        self._create_posts(operation)  # Placeholder
    
    def _delete_comments(self, operation: BulkOperation):
        """Delete comments in bulk"""
        self._create_posts(operation)  # Placeholder
    
    def _import_comments(self, operation: BulkOperation):
        """Import comments in bulk"""
        self._create_posts(operation)  # Placeholder
    
    def _export_comments(self, operation: BulkOperation):
        """Export comments in bulk"""
        self._create_posts(operation)  # Placeholder
