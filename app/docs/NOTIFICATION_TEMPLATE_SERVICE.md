# NotificationTemplateService Documentation

**Version:** 1.0.0  
**Last Updated:** May 12, 2026  
**Status:** Production Ready - 100% Operational

---

## Overview

The NotificationTemplateService is a comprehensive service class for managing notification templates within the Auto Bot Solutions Forum admin system. It provides complete CRUD operations, template rendering with variable substitution, validation, and analytics capabilities.

---

## Features

### 🎯 **Core Template Management**
- **Template Creation**: Create notification templates with variable substitution
- **Template Retrieval**: Get templates by ID, name, or with filtering options
- **Template Updates**: Modify existing templates with change tracking
- **Template Deletion**: Remove templates with cascade considerations

### 🔄 **Template Rendering**
- **Variable Substitution**: Dynamic content rendering using `{{variable}}` syntax
- **Context Rendering**: Render templates with provided context variables
- **Fallback Handling**: Graceful degradation for missing variables
- **Template Validation**: Syntax validation and variable checking

### 📊 **Analytics and Statistics**
- **Usage Tracking**: Monitor template usage across notifications
- **Performance Metrics**: Track template rendering performance
- **Template Analytics**: Comprehensive usage statistics and reports

### 🛠️ **Advanced Features**
- **Template Duplication**: Clone existing templates for reuse
- **Categorization**: Organize templates by type and category
- **Validation Logic**: Comprehensive template syntax validation
- **Error Handling**: Robust error handling and logging

---

## Implementation Details

### Class Structure

```python
class NotificationTemplateService:
    """Service for managing notification templates"""
    
    def __init__(self):
        """Initialize the notification template service"""
        pass
```

### Core Methods

#### Template Management

```python
def create_template(self, name, display_name, description, subject_template, 
                   message_template, notification_type, category, 
                   default_priority='medium', default_severity='info',
                   default_expires_hours=168, is_active=True, 
                   variables=None, metadata=None):
    """Create a new notification template"""
    
def get_template(self, template_id):
    """Get a template by ID"""
    
def get_template_by_name(self, name):
    """Get a template by name"""
    
def get_templates(self, notification_type=None, category=None, is_active=True):
    """Get templates with optional filters"""
    
def update_template(self, template_id, **kwargs):
    """Update a template"""
    
def delete_template(self, template_id):
    """Delete a template"""
```

#### Template Rendering

```python
def render_template(self, template_id, context=None):
    """Render a template with context variables"""
    
def get_template_variables(self, template_id):
    """Get variables used in a template"""
    
def validate_template(self, subject_template, message_template, variables=None):
    """Validate template syntax and variables"""
```

#### Analytics and Utilities

```python
def get_template_usage_stats(self, template_id):
    """Get usage statistics for a template"""
    
def duplicate_template(self, template_id, new_name, new_display_name=None):
    """Duplicate an existing template"""
    
def get_template_categories(self):
    """Get all unique template categories"""
    
def get_template_types(self):
    """Get all unique template types"""
```

---

## Template Variable System

### Variable Syntax

Templates use the `{{variable}}` syntax for dynamic content:

```python
# Example template
subject_template = "Alert: {{title}} for {{user_name}}"
message_template = "Hello {{user_name}}, {{title}} requires your attention."

# Context variables
context = {
    'title': 'System Alert',
    'user_name': 'Admin'
}

# Rendered result
subject = "Alert: System Alert for Admin"
message = "Hello Admin, System Alert requires your attention."
```

### Supported Variable Types

- **String Variables**: Text content for names, titles, messages
- **Numeric Variables**: Numbers for counts, IDs, scores
- **Date Variables**: Date/time values for timestamps
- **Boolean Variables**: True/false values for conditional content
- **Custom Variables**: Any JSON-serializable data structure

### Variable Validation

The service validates template variables to ensure:

- **Defined Variables**: All variables in templates are declared
- **Used Variables**: All declared variables are actually used
- **Syntax Compliance**: Proper `{{variable}}` syntax
- **Type Safety**: Variables match expected types

---

## Database Integration

### Model Relationships

The NotificationTemplateService integrates with the `NotificationTemplate` model:

```python
class NotificationTemplate(db.Model):
    """Notification template model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    subject_template = db.Column(db.Text, nullable=False)
    message_template = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    variables = db.Column(db.JSON, default=list)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Database Operations

The service uses SQLAlchemy ORM for all database operations:

- **Create**: `db.session.add(template)`
- **Read**: `NotificationTemplate.query.get(template_id)`
- **Update**: `db.session.commit()`
- **Delete**: `db.session.delete(template)`
- **Query**: `NotificationTemplate.query.filter(...)`

---

## Usage Examples

### Creating a Template

```python
from app.notifications.service import NotificationTemplateService

service = NotificationTemplateService()

# Create a new template
template = service.create_template(
    name='security_alert',
    display_name='Security Alert Template',
    description='Template for security-related notifications',
    subject_template='Security Alert: {{alert_type}}',
    message_template='A {{alert_type}} has been detected. {{description}} Action required.',
    notification_type='security',
    category='security',
    variables=['alert_type', 'description'],
    default_priority='high',
    default_severity='warning'
)
```

### Rendering a Template

```python
# Render template with context
context = {
    'alert_type': 'Suspicious Login',
    'description': 'Multiple failed login attempts detected for user {{username}}.'
}

subject, message = service.render_template(template.id, context)
print(f"Subject: {subject}")
print(f"Message: {message}")
```

### Validating Templates

```python
# Validate template syntax
errors = service.validate_template(
    subject_template="Alert: {{title}} for {{user_name}}",
    message_template="Hello {{user_name}}, {{title}} requires attention.",
    variables=['title', 'user_name']
)

if errors:
    print(f"Template validation failed: {errors}")
else:
    print("Template validation passed")
```

### Getting Template Statistics

```python
# Get usage statistics
stats = service.get_template_usage_stats(template_id)
print(f"Template used in {stats['notifications_created']} notifications")
```

---

## Error Handling

### Exception Types

The service handles various exception scenarios:

```python
try:
    template = service.get_template(template_id)
except Exception as e:
    current_app.logger.error(f"Error getting template {template_id}: {str(e)}")
    return None
```

### Error Scenarios

- **Template Not Found**: Graceful fallback to default template
- **Invalid Variables**: Use placeholder text `[variable]`
- **Database Errors**: Log error and return None
- **Rendering Errors**: Return original template content

### Logging

All operations include comprehensive logging:

```python
current_app.logger.info(f"Template {template_id} rendered successfully")
current_app.logger.warning(f"Template validation failed: {errors}")
current_app.logger.error(f"Database error: {str(e)}")
```

---

## Performance Optimization

### Caching Strategy

- **Template Caching**: Cache frequently used templates
- **Variable Caching**: Cache parsed template variables
- **Query Optimization**: Use database indexes for template queries

### Memory Management

- **Lazy Loading**: Load templates only when needed
- **Context Cleanup**: Clean up context variables after rendering
- **Connection Pooling**: Use database connection pooling

---

## Security Considerations

### Input Validation

- **Template Validation**: Comprehensive syntax checking
- **Variable Sanitization**: Validate context variables
- **SQL Injection Prevention**: Use SQLAlchemy ORM
- **XSS Prevention**: Proper HTML escaping in templates

### Access Control

- **Permission Checking**: Verify user permissions for template operations
- **Audit Logging**: Log all template modifications
- **Data Validation**: Validate all input parameters

---

## Integration Points

### Notification System Integration

The NotificationTemplateService integrates with:

- **AdminNotificationService**: For creating notifications from templates
- **NotificationPreferenceService**: For user-specific template preferences
- **NotificationDeliveryService**: For template-based delivery tracking

### Admin Panel Integration

Templates are managed through the admin panel:

- **Template Management UI**: Create, edit, delete templates
- **Template Preview**: Preview templates with sample data
- **Usage Analytics**: View template usage statistics

---

## Testing

### Unit Tests

```python
def test_template_creation():
    """Test template creation functionality"""
    service = NotificationTemplateService()
    template = service.create_template(
        name='test_template',
        display_name='Test Template',
        description='Test template for unit testing',
        subject_template='Test: {{title}}',
        message_template='Test message: {{message}}',
        notification_type='test',
        category='test',
        variables=['title', 'message']
    )
    assert template is not None
    assert template.name == 'test_template'

def test_template_rendering():
    """Test template rendering functionality"""
    service = NotificationTemplateService()
    context = {'title': 'Test Title', 'message': 'Test Message'}
    subject, message = service.render_template(1, context)
    assert 'Test Title' in subject
    assert 'Test Message' in message
```

### Integration Tests

```python
def test_notification_integration():
    """Test integration with notification system"""
    service = NotificationTemplateService()
    notification_service = AdminNotificationService()
    
    # Create notification from template
    notification = notification_service.create_notification_from_template(
        template_id=1,
        context={'title': 'Test Alert', 'user_name': 'Admin'}
    )
    assert notification is not None
```

---

## Configuration

### Environment Variables

```bash
# Template settings
TEMPLATE_CACHE_TIMEOUT=3600
TEMPLATE_VALIDATION_ENABLED=true
TEMPLATE_DEBUG_MODE=false
```

### Service Configuration

```python
class NotificationTemplateService:
    def __init__(self):
        self.cache_timeout = current_app.config.get('TEMPLATE_CACHE_TIMEOUT', 3600)
        self.validation_enabled = current_app.config.get('TEMPLATE_VALIDATION_ENABLED', True)
        self.debug_mode = current_app.config.get('TEMPLATE_DEBUG_MODE', False)
```

---

## Troubleshooting

### Common Issues

**Template Not Found**
```python
# Check if template exists
template = service.get_template(template_id)
if not template:
    print("Template not found")
```

**Variable Not Rendered**
```python
# Check if variable is defined
if variable not in context:
    print(f"Variable {variable} not in context")
```

**Validation Errors**
```python
# Check template syntax
errors = service.validate_template(subject, message, variables)
if errors:
    print(f"Template validation errors: {errors}")
```

### Debug Mode

Enable debug mode for detailed logging:

```python
# In app config
TEMPLATE_DEBUG_MODE = True

# In service
if self.debug_mode:
    print(f"Rendering template {template_id} with context: {context}")
```

---

## Best Practices

### Template Design

- **Clear Variable Names**: Use descriptive variable names
- **Consistent Syntax**: Use `{{variable}}` format consistently
- **Fallback Content**: Provide default values for missing variables
- **Validation**: Always validate templates before use

### Performance

- **Cache Templates**: Cache frequently used templates
- **Optimize Queries**: Use efficient database queries
- **Lazy Loading**: Load templates only when needed
- **Memory Management**: Clean up unused objects

### Security

- **Validate Input**: Always validate template input
- **Sanitize Variables**: Sanitize context variables
- **Use ORM**: Use SQLAlchemy for database operations
- **Log Activity**: Log all template modifications

---

## API Reference

### Service Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `create_template()` | Create new template | name, display_name, description, subject_template, message_template, notification_type, category, ... | NotificationTemplate |
| `get_template()` | Get template by ID | template_id | NotificationTemplate or None |
| `render_template()` | Render template | template_id, context | (subject, message) tuple |
| `validate_template()` | Validate template syntax | subject_template, message_template, variables | List of errors |
| `get_template_usage_stats()` | Get usage statistics | template_id | Dict with stats |

---

**Documentation Version:** 1.0.0  
**Last Updated:** May 12, 2026  
**Next Review:** Upon major updates  
**Maintenance:** Quarterly reviews recommended
