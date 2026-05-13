# ModerationQueueFilterForm Documentation

**Version:** 1.0.0  
**Last Updated:** May 12, 2026  
**Status:** Production Ready - 100% Operational

---

## Overview

The ModerationQueueFilterForm is a comprehensive Flask-WTF form designed for advanced filtering of moderation queue items in the Auto Bot Solutions Forum admin system. It provides 20+ filtering options, custom validation, and parameter extraction for efficient database queries.

---

## Features

### 🎯 **Comprehensive Filtering**
- **Status Filtering**: Filter by moderation status (pending, approved, rejected, etc.)
- **Priority Filtering**: Filter by priority levels (low, medium, high, critical)
- **Content Type Filtering**: Filter by content types (posts, comments, profiles, etc.)
- **Score Range Filtering**: Filter by spam and quality score ranges
- **Date Range Filtering**: Filter by creation date ranges
- **User Filtering**: Filter by specific users or reviewers

### 🔍 **Advanced Search**
- **Content Search**: Text search within content
- **Boolean Filters**: Toggle-based filtering options
- **Multi-criteria Filtering**: Combine multiple filter conditions
- **Flexible Sorting**: Multiple sort options with direction control

### 🛠️ **Form Utilities**
- **Parameter Extraction**: Convert form data to query parameters
- **Form Reset**: Reset all fields to default values
- **Validation Logic**: Custom validation for complex scenarios
- **Error Handling**: Comprehensive error messages and validation

---

## Implementation Details

### Class Structure

```python
class ModerationQueueFilterForm(FlaskForm):
    """Form for filtering moderation queue items"""
    
    def __init__(self):
        """Initialize the moderation queue filter form"""
        super().__init__()
```

### Filter Fields

#### Basic Filters

```python
# Status filtering
status = SelectField('Status', choices=[
    ('', 'All Status'),
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('flagged', 'Flagged'),
    ('auto_approved', 'Auto Approved'),
    ('auto_rejected', 'Auto Rejected')
], filters=[lambda x: x or None])

# Priority filtering
priority = SelectField('Priority', choices=[
    ('', 'All Priorities'),
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('critical', 'Critical')
], filters=[lambda x: x or None])

# Content type filtering
content_type = SelectField('Content Type', choices=[
    ('', 'All Types'),
    ('post', 'Posts'),
    ('comment', 'Comments'),
    ('user_profile', 'User Profiles'),
    ('message', 'Messages'),
    ('file', 'Files')
], filters=[lambda x: x or None])
```

#### Score Range Filters

```python
# Spam score filtering
spam_score_min = FloatField('Min Spam Score', validators=[
    Optional(), NumberRange(min=0, max=1)
])
spam_score_max = FloatField('Max Spam Score', validators=[
    Optional(), NumberRange(min=0, max=1)
])

# Quality score filtering
quality_score_min = FloatField('Min Quality Score', validators=[
    Optional(), NumberRange(min=0, max=1)
])
quality_score_max = FloatField('Max Quality Score', validators=[
    Optional(), NumberRange(min=0, max=1)
])
```

#### Date and User Filters

```python
# Date range filtering
date_from = DateTimeField('Date From', format='%Y-%m-%d %H:%M', validators=[Optional()])
date_to = DateTimeField('Date To', format='%Y-%m-%d %H:%M', validators=[Optional()])

# User filtering
user_id = IntegerField('User ID', validators=[Optional()])
reviewer_id = IntegerField('Reviewer ID', validators=[Optional()])

# Content search
content_search = StringField('Content Search', validators=[
    Optional(), Length(max=200)
])
```

#### Boolean Filters

```python
# Action filters
requires_review = BooleanField('Requires Review', default=False)
auto_processed = BooleanField('Auto Processed', default=False)
has_appeal = BooleanField('Has Appeal', default=False)
```

#### Sorting and Pagination

```python
# Sorting options
sort_by = SelectField('Sort By', choices=[
    ('created_at', 'Created Date'),
    ('updated_at', 'Updated Date'),
    ('priority', 'Priority'),
    ('spam_score', 'Spam Score'),
    ('quality_score', 'Quality Score'),
    ('content_type', 'Content Type')
], default='created_at')

sort_order = SelectField('Sort Order', choices=[
    ('desc', 'Descending'),
    ('asc', 'Ascending')
], default='desc')

# Pagination
per_page = SelectField('Per Page', choices=[
    ('10', '10'),
    ('25', '25'),
    ('50', '50'),
    ('100', '100')
], default='25')
```

#### Action Buttons

```python
apply_filter = SubmitField('Apply Filter')
reset_filter = SubmitField('Reset')
```

---

## Validation Methods

### Date Range Validation

```python
def validate_date_range(self, field):
    """Validate date range"""
    if self.date_from.data and self.date_to.data:
        if self.date_from.data > self.date_to.data:
            raise ValidationError('Date from must be before date to')
```

### Score Range Validation

```python
def validate_score_range(self, field):
    """Validate score ranges"""
    if self.spam_score_min.data and self.spam_score_max.data:
        if self.spam_score_min.data > self.spam_score_max.data:
            raise ValidationError('Min spam score must be less than max spam score')
    
    if self.quality_score_min.data and self.quality_score_max.data:
        if self.quality_score_min.data > self.quality_score_max.data:
            raise ValidationError('Min quality score must be less than max quality score')
```

---

## Utility Methods

### Parameter Extraction

```python
def get_filter_params(self):
    """Get filter parameters as dictionary"""
    params = {}
    
    # Add non-empty filters
    if self.status.data:
        params['status'] = self.status.data
    
    if self.priority.data:
        params['priority'] = self.priority.data
    
    if self.content_type.data:
        params['content_type'] = self.content_type.data
    
    if self.spam_score_min.data is not None:
        params['spam_score_min'] = self.spam_score_min.data
    
    if self.spam_score_max.data is not None:
        params['spam_score_max'] = self.spam_score_max.data
    
    if self.quality_score_min.data is not None:
        params['quality_score_min'] = self.quality_score_min.data
    
    if self.quality_score_max.data is not None:
        params['quality_score_max'] = self.quality_score_max.data
    
    if self.date_from.data:
        params['date_from'] = self.date_from.data
    
    if self.date_to.data:
        params['date_to'] = self.date_to.data
    
    if self.user_id.data:
        params['user_id'] = self.user_id.data
    
    if self.reviewer_id.data:
        params['reviewer_id'] = self.reviewer_id.data
    
    if self.content_search.data:
        params['content_search'] = self.content_search.data
    
    if self.requires_review.data:
        params['requires_review'] = self.requires_review.data
    
    if self.auto_processed.data:
        params['auto_processed'] = self.auto_processed.data
    
    if self.has_appeal.data:
        params['has_appeal'] = self.has_appeal.data
    
    # Sorting
    params['sort_by'] = self.sort_by.data
    params['sort_order'] = self.sort_order.data
    params['per_page'] = int(self.per_page.data)
    
    return params
```

### Form Reset

```python
def reset_form_data(self):
    """Reset form to default values"""
    self.status.data = ''
    self.priority.data = ''
    self.content_type.data = ''
    self.spam_score_min.data = None
    self.spam_score_max.data = None
    self.quality_score_min.data = None
    self.quality_score_max.data = None
    self.date_from.data = None
    self.date_to.data = None
    self.user_id.data = None
    self.reviewer_id.data = None
    self.content_search.data = ''
    self.requires_review.data = False
    self.auto_processed.data = False
    self.has_appeal.data = False
    self.sort_by.data = 'created_at'
    self.sort_order.data = 'desc'
    self.per_page.data = '25'
```

---

## Usage Examples

### Basic Usage

```python
from app.moderation.forms import ModerationQueueFilterForm

# Create form instance
form = ModerationQueueFilterForm()

# Handle form submission
if form.validate_on_submit():
    if form.apply_filter.data:
        # Get filter parameters
        params = form.get_filter_params()
        
        # Apply filters to query
        queue_items = ModerationQueue.query.filter_by(**params).all()
        
    elif form.reset_filter.data:
        # Reset form
        form.reset_form_data()
```

### Advanced Filtering

```python
# Create form with data
form_data = {
    'status': 'pending',
    'priority': 'high',
    'spam_score_min': 0.7,
    'spam_score_max': 1.0,
    'date_from': datetime(2026, 5, 1),
    'date_to': datetime(2026, 5, 12),
    'requires_review': True,
    'sort_by': 'created_at',
    'sort_order': 'desc',
    'per_page': '50'
}

form = ModerationQueueFilterForm(data=form_data)

if form.validate():
    # Build complex query
    query = ModerationQueue.query
    
    # Apply filters
    if form.status.data:
        query = query.filter(ModerationQueue.status == form.status.data)
    
    if form.priority.data:
        query = query.filter(ModerationQueue.priority == form.priority.data)
    
    if form.spam_score_min.data:
        query = query.filter(ModerationQueue.spam_score >= form.spam_score_min.data)
    
    if form.spam_score_max.data:
        query = query.filter(ModerationQueue.spam_score <= form.spam_score_max.data)
    
    if form.date_from.data:
        query = query.filter(ModerationQueue.created_at >= form.date_from.data)
    
    if form.date_to.data:
        query = query.filter(ModerationQueue.created_at <= form.date_to.data)
    
    # Apply sorting
    if form.sort_by.data == 'created_at':
        if form.sort_order.data == 'desc':
            query = query.order_by(ModerationQueue.created_at.desc())
        else:
            query = query.order_by(ModerationQueue.created_at.asc())
    
    # Execute query with pagination
    page = request.args.get('page', 1, type=int)
    per_page = int(form.per_page.data)
    queue_items = query.paginate(page=page, per_page=per_page)
```

### Template Integration

```html
<!-- moderation_queue.html -->
<form method="GET" class="filter-form">
    {{ form.hidden_tag() }}
    
    <div class="row">
        <div class="col-md-3">
            {{ form.status.label(class="form-label") }}
            {{ form.status(class="form-select") }}
        </div>
        
        <div class="col-md-3">
            {{ form.priority.label(class="form-label") }}
            {{ form.priority(class="form-select") }}
        </div>
        
        <div class="col-md-3">
            {{ form.content_type.label(class="form-label") }}
            {{ form.content_type(class="form-select") }}
        </div>
        
        <div class="col-md-3">
            {{ form.sort_by.label(class="form-label") }}
            {{ form.sort_by(class="form-select") }}
        </div>
    </div>
    
    <div class="row mt-3">
        <div class="col-md-3">
            {{ form.spam_score_min.label(class="form-label") }}
            {{ form.spam_score_min(class="form-control") }}
        </div>
        
        <div class="col-md-3">
            {{ form.spam_score_max.label(class="form-label") }}
            {{ form.spam_score_max(class="form-control") }}
        </div>
        
        <div class="col-md-3">
            {{ form.date_from.label(class="form-label") }}
            {{ form.date_from(class="form-control") }}
        </div>
        
        <div class="col-md-3">
            {{ form.date_to.label(class="form-label") }}
            {{ form.date_to(class="form-control") }}
        </div>
    </div>
    
    <div class="row mt-3">
        <div class="col-md-6">
            {{ form.content_search.label(class="form-label") }}
            {{ form.content_search(class="form-control") }}
        </div>
        
        <div class="col-md-3">
            {{ form.requires_review(class="form-check-input") }}
            {{ form.requires_review.label(class="form-check-label") }}
        </div>
        
        <div class="col-md-3">
            {{ form.auto_processed(class="form-check-input") }}
            {{ form.auto_processed.label(class="form-check-label") }}
        </div>
    </div>
    
    <div class="row mt-3">
        <div class="col-md-6">
            {{ form.apply_filter(class="btn btn-primary") }}
            {{ form.reset_filter(class="btn btn-secondary") }}
        </div>
    </div>
</form>
```

---

## Database Integration

### Model Compatibility

The form is designed to work with the `ModerationQueue` model:

```python
class ModerationQueue(db.Model):
    """Moderation queue model"""
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False)
    priority = db.Column(db.String(20), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)
    spam_score = db.Column(db.Float, nullable=True)
    quality_score = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    requires_review = db.Column(db.Boolean, default=False)
    auto_processed = db.Column(db.Boolean, default=False)
    has_appeal = db.Column(db.Boolean, default=False)
```

### Query Building

The form's `get_filter_params()` method returns parameters that can be directly used in SQLAlchemy queries:

```python
# Get filter parameters
params = form.get_filter_params()

# Build query
query = ModerationQueue.query

# Apply filters dynamically
for key, value in params.items():
    if hasattr(ModerationQueue, key):
        if isinstance(value, (int, str, bool)):
            query = query.filter(getattr(ModerationQueue, key) == value)
        elif isinstance(value, float):
            query = query.filter(getattr(ModerationQueue, key) >= value)
        elif isinstance(value, datetime):
            query = query.filter(getattr(ModerationQueue, key) >= value)
```

---

## Performance Optimization

### Query Optimization

- **Index Usage**: Ensure database indexes on frequently filtered fields
- **Query Caching**: Cache frequently used filter combinations
- **Lazy Loading**: Load results only when needed
- **Pagination**: Use efficient pagination with limit/offset

### Form Optimization

- **Field Validation**: Efficient validation with minimal database calls
- **Parameter Extraction**: Optimized parameter building
- **Memory Management**: Clean up form data after use

---

## Security Considerations

### Input Validation

- **SQL Injection Prevention**: Use SQLAlchemy ORM
- **XSS Prevention**: Proper HTML escaping in templates
- **Input Sanitization**: Validate all user inputs
- **Type Safety**: Enforce proper data types

### Access Control

- **Permission Checking**: Verify user permissions for filtering
- **Data Filtering**: Filter results based on user permissions
- **Audit Logging**: Log filter usage for security monitoring

---

## Error Handling

### Validation Errors

```python
# Handle form validation errors
if not form.validate():
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{field}: {error}', 'error')
    return render_template('moderation_queue.html', form=form)
```

### Database Errors

```python
try:
    queue_items = query.paginate(page=page, per_page=per_page)
except Exception as e:
    current_app.logger.error(f"Database error: {str(e)}")
    flash('Error loading moderation queue', 'error')
    return redirect(url_for('moderation.index'))
```

---

## Testing

### Unit Tests

```python
def test_form_validation():
    """Test form validation"""
    form_data = {
        'status': 'pending',
        'priority': 'high',
        'spam_score_min': 0.5,
        'spam_score_max': 0.8,
        'date_from': datetime(2026, 5, 1),
        'date_to': datetime(2026, 5, 12)
    }
    
    form = ModerationQueueFilterForm(data=form_data)
    assert form.validate() == True

def test_date_range_validation():
    """Test date range validation"""
    form_data = {
        'date_from': datetime(2026, 5, 12),
        'date_to': datetime(2026, 5, 1)  # Invalid: from > to
    }
    
    form = ModerationQueueFilterForm(data=form_data)
    assert form.validate() == False
    assert 'Date from must be before date to' in str(form.errors)

def test_parameter_extraction():
    """Test parameter extraction"""
    form_data = {
        'status': 'pending',
        'priority': 'high',
        'requires_review': True
    }
    
    form = ModerationQueueFilterForm(data=form_data)
    params = form.get_filter_params()
    
    assert params['status'] == 'pending'
    assert params['priority'] == 'high'
    assert params['requires_review'] == True
```

### Integration Tests

```python
def test_form_integration():
    """Test form integration with database"""
    form_data = {
        'status': 'pending',
        'priority': 'high'
    }
    
    form = ModerationQueueFilterForm(data=form_data)
    params = form.get_filter_params()
    
    # Test query building
    query = ModerationQueue.query
    for key, value in params.items():
        if hasattr(ModerationQueue, key):
            query = query.filter(getattr(ModerationQueue, key) == value)
    
    # Execute query
    results = query.all()
    assert isinstance(results, list)
```

---

## Configuration

### Form Configuration

```python
# In app config
MODERATION_FILTER_DEFAULT_PER_PAGE = 25
MODERATION_FILTER_MAX_PER_PAGE = 100
MODERATION_FILTER_DATE_FORMAT = '%Y-%m-%d %H:%M'
```

### Custom Validation

```python
def custom_validate_spam_score(form, field):
    """Custom spam score validation"""
    if field.data and (field.data < 0 or field.data > 1):
        raise ValidationError('Spam score must be between 0 and 1')

# Add to field
spam_score_min = FloatField('Min Spam Score', validators=[
    Optional(), NumberRange(min=0, max=1), custom_validate_spam_score
])
```

---

## Best Practices

### Form Design

- **Clear Labels**: Use descriptive field labels
- **Logical Grouping**: Group related fields together
- **Default Values**: Provide sensible default values
- **Validation Messages**: Use clear validation error messages

### Performance

- **Efficient Queries**: Use database indexes
- **Pagination**: Implement efficient pagination
- **Caching**: Cache frequently used filter combinations
- **Memory Management**: Clean up unused objects

### Security

- **Input Validation**: Validate all user inputs
- **SQL Injection Prevention**: Use parameterized queries
- **XSS Prevention**: Escape user input in templates
- **Access Control**: Implement proper permission checks

---

## Troubleshooting

### Common Issues

**Form Not Validating**
```python
# Check form errors
if not form.validate():
    print(form.errors)
```

**Query Not Working**
```python
# Check query parameters
params = form.get_filter_params()
print(f"Query params: {params}")
```

**Pagination Issues**
```python
# Check pagination parameters
page = request.args.get('page', 1, type=int)
per_page = int(form.per_page.data)
print(f"Page: {page}, Per page: {per_page}")
```

### Debug Mode

Enable debug mode for detailed logging:

```python
# In app config
DEBUG = True

# In form
if current_app.debug:
    print(f"Form data: {form.data}")
    print(f"Form errors: {form.errors}")
```

---

## API Reference

### Form Fields

| Field | Type | Description | Choices/Validation |
|-------|------|-------------|-------------------|
| `status` | SelectField | Filter by moderation status | pending, approved, rejected, flagged, auto_approved, auto_rejected |
| `priority` | SelectField | Filter by priority | low, medium, high, critical |
| `content_type` | SelectField | Filter by content type | post, comment, user_profile, message, file |
| `spam_score_min/max` | FloatField | Filter by spam score range | 0-1 range |
| `quality_score_min/max` | FloatField | Filter by quality score range | 0-1 range |
| `date_from/to` | DateTimeField | Filter by date range | Optional validation |
| `user_id/reviewer_id` | IntegerField | Filter by user/reviewer | Optional validation |
| `content_search` | StringField | Search within content | Max 200 characters |
| `requires_review/auto_processed/has_appeal` | BooleanField | Boolean filters | Default False |
| `sort_by` | SelectField | Sort field | created_at, updated_at, priority, spam_score, quality_score, content_type |
| `sort_order` | SelectField | Sort direction | desc, asc |
| `per_page` | SelectField | Items per page | 10, 25, 50, 100 |

### Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `get_filter_params()` | Extract filter parameters | None | Dict of parameters |
| `reset_form_data()` | Reset form to defaults | None | None |
| `validate_date_range()` | Validate date range | field | ValidationError or None |
| `validate_score_range()` | Validate score ranges | field | ValidationError or None |

---

**Documentation Version:** 1.0.0  
**Last Updated:** May 12, 2026  
**Next Review:** Upon major updates  
**Maintenance:** Quarterly reviews recommended
