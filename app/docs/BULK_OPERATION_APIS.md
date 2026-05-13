# Bulk Operation APIs Documentation

## Overview

The Bulk Operation APIs provide comprehensive batch processing capabilities with file import/export, data validation, progress tracking, and error handling. This system enables efficient processing of large datasets with support for multiple file formats and parallel processing.

## Architecture

### Core Components

1. **BulkOperationManager** - Central operation management
2. **BulkProcessor** - Data processing and transformation
3. **BulkValidators** - Data validation and sanitization
4. **BulkDecorators** - Flask route decorators
5. **BulkRoutes** - Management and monitoring endpoints

### Processing Flow

```
Data Input → Validation → Processing → Batching → Execution → Results → Reporting
```

## Features

### Batch Processing

- **Parallel Processing**: Multi-threaded batch execution
- **Configurable Batching**: Customizable batch sizes
- **Progress Tracking**: Real-time progress monitoring
- **Error Handling**: Comprehensive error management
- **Retry Logic**: Automatic retry for failed operations

### File Operations

- **Multiple Formats**: CSV, JSON, Excel (XLSX/XLS) support
- **File Upload**: Secure file upload with validation
- **Data Import**: Import data from various file formats
- **Data Export**: Export data in multiple formats
- **Template Generation**: Generate import templates

### Data Validation

- **Field Validation**: Type and format validation
- **Business Rules**: Custom business rule validation
- **Data Sanitization**: Input sanitization and cleaning
- **Duplicate Detection**: Duplicate data detection
- **Relationship Validation**: Data relationship validation

### Operation Management

- **Operation Queuing**: Queue multiple operations
- **Concurrent Control**: Manage concurrent operations
- **Cancellation**: Cancel running operations
- **History Tracking**: Operation history and logs
- **Performance Metrics**: Performance monitoring

## Implementation

### File Structure

```
app/api/bulk/
├── __init__.py                 # Package initialization
├── bulk_manager.py           # Central operation management
├── bulk_processor.py         # Data processing and transformation
├── bulk_validators.py        # Data validation and sanitization
├── bulk_decorators.py        # Flask route decorators
└── bulk_routes.py            # Management endpoints
```

### Bulk Operation Manager

```python
from app.api.bulk import BulkOperationManager, BulkOperationConfig, BulkOperationType

# Initialize bulk manager
bulk_manager = BulkOperationManager()

# Create operation
config = BulkOperationConfig(
    operation_type=BulkOperationType.CREATE,
    resource_type='posts',
    batch_size=100,
    max_workers=4,
    continue_on_error=True
)

operation_id = bulk_manager.create_operation(config, data)
result = bulk_manager.execute_operation(operation_id)
```

### Data Processing

```python
from app.api.bulk import BulkProcessor

# Initialize processor
processor = BulkProcessor()

# Process data
result = processor.process_operation(operation)
print(f"Processed: {result['processed']}")
print(f"Successful: {result['successful']}")
print(f"Failed: {result['failed']}")
```

### Data Validation

```python
from app.api.bulk import get_validator

# Get validator for resource type
validator = get_validator('posts')

# Validate data
validation_result = validator.validate(data)
if not validation_result['valid']:
    print(f"Validation errors: {validation_result['errors']}")
```

## API Endpoints

### Operation Management

- `GET /api/bulk/operations` - List all bulk operations
- `GET /api/bulk/operations/{operation_id}` - Get operation details
- `POST /api/bulk/operations/{operation_id}/cancel` - Cancel operation
- `GET /api/bulk/operations/{operation_id}/progress` - Get operation progress
- `GET /api/bulk/operations/{operation_id}/errors` - Get operation errors

### File Operations

- `POST /api/bulk/upload/{resource_type}` - Upload file for bulk operation
- `POST /api/bulk/export/{resource_type}` - Export data to file
- `GET /api/bulk/templates/{resource_type}` - Get import templates

### Validation and Configuration

- `POST /api/bulk/validate/{resource_type}` - Validate bulk data
- `GET /api/bulk/config` - Get bulk operation configuration
- `GET /api/bulk/stats` - Get bulk operation statistics
- `POST /api/bulk/cleanup` - Clean up old operations

## Usage Examples

### Bulk Create Operations

```python
# Create multiple posts
data = [
    {
        'title': 'Python Tutorial 1',
        'content': 'Learn Python basics',
        'author_id': 1,
        'status': 'published'
    },
    {
        'title': 'Python Tutorial 2',
        'content': 'Advanced Python concepts',
        'author_id': 2,
        'status': 'published'
    }
]

config = BulkOperationConfig(
    operation_type=BulkOperationType.CREATE,
    resource_type='posts',
    batch_size=50,
    max_workers=2
)

operation_id = bulk_manager.create_operation(config, data)
result = bulk_manager.execute_operation(operation_id)
```

### File Import

```python
# Upload CSV file for import
files = {'file': open('posts.csv', 'rb')}
data = {
    'resource_type': 'posts',
    'operation_type': 'create',
    'batch_size': 100
}

response = requests.post('http://localhost:5000/api/bulk/upload/posts', 
                        files=files, data=data)

# Get operation status
operation_id = response.json()['data']['operation_id']
status = requests.get(f'http://localhost:5000/api/bulk/operations/{operation_id}/progress')
```

### Data Export

```python
# Export posts to CSV
export_data = {
    'format': 'csv',
    'filters': {
        'status': 'published',
        'created_after': '2024-01-01'
    }
}

response = requests.post('http://localhost:5000/api/bulk/export/posts', 
                        json=export_data)

# Download file
file_content = response.json()['data']['file_content']
with open('posts_export.csv', 'w') as f:
    f.write(file_content)
```

## Operation Types

### Create Operations

```python
# Bulk create
config = BulkOperationConfig(
    operation_type=BulkOperationType.CREATE,
    resource_type='posts',
    validate_before_execute=True,
    generate_report=True
)
```

### Update Operations

```python
# Bulk update
config = BulkOperationConfig(
    operation_type=BulkOperationType.UPDATE,
    resource_type='posts',
    batch_size=50,
    retry_failed=True,
    max_retries=3
)
```

### Delete Operations

```python
# Bulk delete
config = BulkOperationConfig(
    operation_type=BulkOperationType.DELETE,
    resource_type='posts',
    continue_on_error=False,
    timeout=600
)
```

### Import Operations

```python
# Bulk import
config = BulkOperationConfig(
    operation_type=BulkOperationType.IMPORT,
    resource_type='posts',
    batch_size=100,
    max_workers=4
)
```

### Export Operations

```python
# Bulk export
config = BulkOperationConfig(
    operation_type=BulkOperationType.EXPORT,
    resource_type='posts',
    generate_report=True
)
```

### Upsert Operations

```python
# Bulk upsert (update or insert)
config = BulkOperationConfig(
    operation_type=BulkOperationType.UPSERT,
    resource_type='posts',
    batch_size=50,
    validate_before_execute=True
)
```

## File Formats

### CSV Format

```python
# CSV file structure
# title,content,author_id,status
"Python Tutorial","Learn Python",1,"published"
"JavaScript Guide","Learn JS",2,"draft"
```

### JSON Format

```python
# JSON file structure
[
    {
        "title": "Python Tutorial",
        "content": "Learn Python",
        "author_id": 1,
        "status": "published"
    },
    {
        "title": "JavaScript Guide",
        "content": "Learn JS",
        "author_id": 2,
        "status": "draft"
    }
]
```

### Excel Format

```python
# Excel file structure
# Columns: title, content, author_id, status
# Row 1: Python Tutorial, Learn Python, 1, published
# Row 2: JavaScript Guide, Learn JS, 2, draft
```

## Data Validation

### Field Validation

```python
# Required fields
validator.add_required_field('title')
validator.add_required_field('content')

# Optional fields
validator.add_optional_field('author_id')
validator.add_optional_field('status')

# Field validators
validator.add_field_validator('title', validate_title)
validator.add_field_validator('email', validate_email)
```

### Custom Validation

```python
# Custom validator
def validate_post_consistency(item):
    errors = []
    
    if item.get('status') == 'published' and not item.get('author_id'):
        errors.append("Published posts must have an author")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

validator.add_custom_validator(validate_post_consistency)
```

### Validation Results

```python
# Validation result format
{
    'valid': True,
    'errors': [],
    'warnings': [],
    'total_items': 100,
    'error_count': 0,
    'warning_count': 5
}
```

## Progress Tracking

### Operation Progress

```python
# Get operation progress
operation = bulk_manager.get_operation(operation_id)
progress = operation.result.get_progress_percentage()
success_rate = operation.result.get_success_rate()

print(f"Progress: {progress}%")
print(f"Success rate: {success_rate}%")
```

### Real-time Updates

```python
# Progress callback
def progress_callback(result):
    print(f"Processed: {result.processed_items}")
    print(f"Successful: {result.successful_items}")
    print(f"Failed: {result.failed_items}")

operation.set_progress_callback(progress_callback)
```

### Progress API

```python
# Progress endpoint response
{
    "success": true,
    "data": {
        "operation_id": "uuid",
        "status": "running",
        "progress": {
            "total_items": 1000,
            "processed_items": 500,
            "successful_items": 480,
            "failed_items": 20,
            "progress_percentage": 50.0,
            "success_rate": 96.0
        },
        "timestamps": {
            "started_at": "2024-05-12T10:00:00Z",
            "estimated_completion": "2024-05-12T10:05:00Z"
        }
    }
}
```

## Error Handling

### Error Types

```python
# Validation errors
{
    "type": "validation_error",
    "message": "Required field missing",
    "field": "title",
    "row_index": 5
}

# Processing errors
{
    "type": "processing_error",
    "message": "Database constraint violation",
    "item": {"title": "Duplicate Title"},
    "row_index": 10
}

# System errors
{
    "type": "system_error",
    "message": "Connection timeout",
    "timestamp": "2024-05-12T10:00:00Z"
}
```

### Error Recovery

```python
# Retry configuration
config = BulkOperationConfig(
    operation_type=BulkOperationType.CREATE,
    resource_type='posts',
    retry_failed=True,
    max_retries=3,
    continue_on_error=True
)
```

### Error Reporting

```python
# Error report format
{
    "operation_id": "uuid",
    "total_errors": 5,
    "errors": [
        {
            "row_index": 1,
            "error": "Invalid email format",
            "data": {"email": "invalid-email"}
        }
    ],
    "error_summary": {
        "validation_errors": 3,
        "processing_errors": 2,
        "system_errors": 0
    }
}
```

## Performance Optimization

### Batch Processing

```python
# Optimize batch size
config = BulkOperationConfig(
    operation_type=BulkOperationType.CREATE,
    resource_type='posts',
    batch_size=100,  # Optimal batch size
    max_workers=4    # Parallel processing
)
```

### Parallel Processing

```python
# Parallel processing configuration
processor = BulkProcessor(max_workers=8)

# Process in parallel
result = processor.process_operation(operation)
```

### Memory Management

```python
# Memory-efficient processing
def process_large_file(file_path):
    """Process large file in chunks"""
    chunk_size = 1000
    
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        chunk = []
        
        for i, row in enumerate(reader):
            chunk.append(row)
            
            if len(chunk) >= chunk_size:
                process_chunk(chunk)
                chunk = []
        
        # Process remaining items
        if chunk:
            process_chunk(chunk)
```

## Configuration

### Bulk Operation Configuration

```python
# app/config.py
BULK_OPERATION_CONFIG = {
    'max_concurrent_operations': 5,
    'default_batch_size': 100,
    'max_batch_size': 1000,
    'default_timeout': 300,
    'max_file_size': 10485760,  # 10MB
    'supported_formats': ['csv', 'json', 'xlsx', 'xls']
}
```

### Processing Configuration

```python
PROCESSING_CONFIG = {
    'default_max_workers': 4,
    'max_max_workers': 10,
    'retry_failed': True,
    'max_retries': 3,
    'continue_on_error': True
}
```

## Client Integration

### JavaScript Client

```javascript
class BulkOperationClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }
    
    async uploadFile(resourceType, file, operationType = 'create') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('operation_type', operationType);
        
        const response = await fetch(
            `${this.baseUrl}/api/bulk/upload/${resourceType}`,
            {
                method: 'POST',
                body: formData
            }
        );
        
        return response.json();
    }
    
    async getOperationProgress(operationId) {
        const response = await fetch(
            `${this.baseUrl}/api/bulk/operations/${operationId}/progress`
        );
        
        return response.json();
    }
    
    async cancelOperation(operationId) {
        const response = await fetch(
            `${this.baseUrl}/api/bulk/operations/${operationId}/cancel`,
            { method: 'POST' }
        );
        
        return response.json();
    }
}

// Usage
const client = new BulkOperationClient('http://localhost:5000');

// Upload file
const fileInput = document.getElementById('file-input');
const file = fileInput.files[0];

client.uploadFile('posts', file, 'create')
    .then(result => {
        const operationId = result.data.operation_id;
        
        // Monitor progress
        const progressInterval = setInterval(() => {
            client.getOperationProgress(operationId)
                .then(progress => {
                    console.log(`Progress: ${progress.data.progress.progress_percentage}%`);
                    
                    if (progress.data.status === 'completed') {
                        clearInterval(progressInterval);
                    }
                });
        }, 1000);
    });
```

### Python Client

```python
import requests
import time

class BulkOperationClient:
    def __init__(self, base_url):
        self.base_url = base_url
    
    def upload_file(self, resource_type, file_path, operation_type='create'):
        """Upload file for bulk operation"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'operation_type': operation_type,
                'batch_size': 100
            }
            
            response = requests.post(
                f'{self.base_url}/api/bulk/upload/{resource_type}',
                files=files,
                data=data
            )
        
        return response.json()
    
    def get_operation_progress(self, operation_id):
        """Get operation progress"""
        response = requests.get(
            f'{self.base_url}/api/bulk/operations/{operation_id}/progress'
        )
        return response.json()
    
    def wait_for_completion(self, operation_id, check_interval=5):
        """Wait for operation completion"""
        while True:
            progress = self.get_operation_progress(operation_id)
            status = progress['data']['status']
            
            print(f"Status: {status}")
            print(f"Progress: {progress['data']['progress']['progress_percentage']:.1f}%")
            
            if status in ['completed', 'failed', 'cancelled']:
                return progress
            
            time.sleep(check_interval)

# Usage
client = BulkOperationClient('http://localhost:5000')

# Upload file
result = client.upload_file('posts', 'posts.csv', 'create')
operation_id = result['data']['operation_id']

# Wait for completion
final_result = client.wait_for_completion(operation_id)
print(f"Final result: {final_result}")
```

## Best Practices

### Data Preparation

1. **Clean Data**: Remove duplicates and invalid data
2. **Format Validation**: Ensure proper data format
3. **Field Mapping**: Map fields correctly
4. **Test Data**: Test with small samples first

### Operation Planning

1. **Batch Size**: Use appropriate batch sizes
2. **Timeout Settings**: Set reasonable timeouts
3. **Error Handling**: Plan for error scenarios
4. **Resource Limits**: Consider system resources

### Performance Optimization

1. **Parallel Processing**: Use multiple workers
2. **Memory Management**: Process in chunks
3. **Database Optimization**: Use efficient queries
4. **Caching**: Cache where appropriate

## Troubleshooting

### Common Issues

1. **File Upload Errors**: Check file format and size
2. **Validation Failures**: Review validation rules
3. **Processing Errors**: Check data integrity
4. **Performance Issues**: Optimize batch sizes

### Debug Mode

```python
# Enable bulk operation debug mode
app.config['BULK_OPERATION_DEBUG'] = True

# View bulk operation logs
import logging
logging.getLogger('app.api.bulk').setLevel(logging.DEBUG)
```

### Error Analysis

```python
# Analyze operation errors
operation = bulk_manager.get_operation(operation_id)
errors = operation.result.errors

# Group errors by type
error_types = {}
for error in errors:
    error_type = error.get('type', 'unknown')
    if error_type not in error_types:
        error_types[error_type] = []
    error_types[error_type].append(error)

print(f"Error summary: {error_types}")
```

## Security Considerations

### File Security

1. **File Validation**: Validate file types and sizes
2. **Malware Scanning**: Scan uploaded files
3. **Access Control**: Restrict file access
4. **Audit Logging**: Log file operations

### Data Security

1. **Input Sanitization**: Sanitize all input data
2. **Permission Checking**: Verify user permissions
3. **Data Encryption**: Encrypt sensitive data
4. **Access Logging**: Log data access

## Future Enhancements

### Planned Features

1. **Advanced Scheduling**: Scheduled bulk operations
2. **Template System**: Advanced template management
3. **Data Transformation**: Complex data transformations
4. **Integration APIs**: External system integration

### Extension Points

1. **Custom Processors**: Additional data processors
2. **Custom Validators**: Additional validation rules
3. **Custom Formats**: Additional file formats
4. **Integration Hooks**: External system hooks

---

**Last Updated**: May 12, 2026  
**Version**: 1.0  
**Status**: Production Ready
