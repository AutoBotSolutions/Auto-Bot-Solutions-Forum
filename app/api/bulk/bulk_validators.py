"""
Bulk Validators

Validation utilities for bulk operations.
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import re
import json

logger = logging.getLogger(__name__)

class BulkValidator:
    """Base class for bulk validators"""
    
    def __init__(self):
        self.required_fields = []
        self.optional_fields = []
        self.field_validators = {}
        self.custom_validators = []
    
    def add_required_field(self, field_name: str):
        """Add required field"""
        self.required_fields.append(field_name)
    
    def add_optional_field(self, field_name: str):
        """Add optional field"""
        self.optional_fields.append(field_name)
    
    def add_field_validator(self, field_name: str, validator: Callable):
        """Add field validator"""
        self.field_validators[field_name] = validator
    
    def add_custom_validator(self, validator: Callable):
        """Add custom validator"""
        self.custom_validators.append(validator)
    
    def validate(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate data"""
        errors = []
        warnings = []
        
        for i, item in enumerate(data):
            item_errors = []
            item_warnings = []
            
            # Check required fields
            for field in self.required_fields:
                if field not in item or item[field] is None:
                    item_errors.append(f"Missing required field: {field}")
            
            # Check field validators
            for field, validator in self.field_validators.items():
                if field in item:
                    try:
                        result = validator(item[field])
                        if not result['valid']:
                            item_errors.extend(result['errors'])
                        if 'warnings' in result:
                            item_warnings.extend(result['warnings'])
                    except Exception as e:
                        item_errors.append(f"Validation error for field {field}: {str(e)}")
            
            # Check custom validators
            for validator in self.custom_validators:
                try:
                    result = validator(item)
                    if not result['valid']:
                        item_errors.extend(result['errors'])
                    if 'warnings' in result:
                        item_warnings.extend(result['warnings'])
                except Exception as e:
                    item_errors.append(f"Custom validation error: {str(e)}")
            
            if item_errors:
                errors.append({
                    'row_index': i,
                    'errors': item_errors,
                    'data': item
                })
            
            if item_warnings:
                warnings.append({
                    'row_index': i,
                    'warnings': item_warnings,
                    'data': item
                })
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'total_items': len(data),
            'error_count': len(errors),
            'warning_count': len(warnings)
        }

class PostValidator(BulkValidator):
    """Validator for post data"""
    
    def __init__(self):
        super().__init__()
        
        # Required fields
        self.add_required_field('title')
        self.add_required_field('content')
        
        # Optional fields
        self.add_optional_field('author_id')
        self.add_optional_field('status')
        self.add_optional_field('tags')
        self.add_optional_field('category_id')
        
        # Field validators
        self.add_field_validator('title', self._validate_title)
        self.add_field_validator('content', self._validate_content)
        self.add_field_validator('author_id', self._validate_author_id)
        self.add_field_validator('status', self._validate_status)
        self.add_field_validator('tags', self._validate_tags)
        self.add_field_validator('category_id', self._validate_category_id)
        
        # Custom validators
        self.add_custom_validator(self._validate_post_consistency)
    
    def _validate_title(self, title: str) -> Dict[str, Any]:
        """Validate title field"""
        errors = []
        warnings = []
        
        if not isinstance(title, str):
            errors.append("Title must be a string")
            return {'valid': False, 'errors': errors}
        
        if len(title.strip()) < 3:
            errors.append("Title must be at least 3 characters long")
        
        if len(title) > 200:
            warnings.append("Title is very long, consider shortening")
        
        # Check for profanity (simplified)
        profanity_patterns = ['spam', 'adult', 'illegal']
        for pattern in profanity_patterns:
            if pattern.lower() in title.lower():
                warnings.append(f"Title contains potentially inappropriate content: {pattern}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_content(self, content: str) -> Dict[str, Any]:
        """Validate content field"""
        errors = []
        warnings = []
        
        if not isinstance(content, str):
            errors.append("Content must be a string")
            return {'valid': False, 'errors': errors}
        
        if len(content.strip()) < 10:
            errors.append("Content must be at least 10 characters long")
        
        if len(content) > 50000:
            warnings.append("Content is very long, consider splitting into multiple posts")
        
        # Check for HTML tags (if not allowed)
        if '<' in content and '>' in content:
            warnings.append("Content contains HTML tags, ensure they are properly escaped")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_author_id(self, author_id: Any) -> Dict[str, Any]:
        """Validate author_id field"""
        errors = []
        
        try:
            author_id = int(author_id)
            if author_id <= 0:
                errors.append("Author ID must be a positive integer")
        except (ValueError, TypeError):
            errors.append("Author ID must be a valid integer")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_status(self, status: str) -> Dict[str, Any]:
        """Validate status field"""
        errors = []
        
        valid_statuses = ['draft', 'published', 'archived', 'deleted']
        if status not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_tags(self, tags: Any) -> Dict[str, Any]:
        """Validate tags field"""
        errors = []
        warnings = []
        
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',')]
        elif isinstance(tags, list):
            tags = [str(tag).strip() for tag in tags]
        else:
            errors.append("Tags must be a string or list")
            return {'valid': False, 'errors': errors}
        
        # Validate individual tags
        for tag in tags:
            if len(tag) < 2:
                errors.append(f"Tag '{tag}' is too short (minimum 2 characters)")
            elif len(tag) > 50:
                warnings.append(f"Tag '{tag}' is very long")
            
            # Check for invalid characters
            if not re.match(r'^[a-zA-Z0-9_\-\s]+$', tag):
                errors.append(f"Tag '{tag}' contains invalid characters")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_category_id(self, category_id: Any) -> Dict[str, Any]:
        """Validate category_id field"""
        errors = []
        
        try:
            category_id = int(category_id)
            if category_id <= 0:
                errors.append("Category ID must be a positive integer")
        except (ValueError, TypeError):
            errors.append("Category ID must be a valid integer")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_post_consistency(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Validate post consistency"""
        errors = []
        warnings = []
        
        # Check if published post has required fields
        if item.get('status') == 'published':
            if not item.get('author_id'):
                errors.append("Published posts must have an author")
            
            if not item.get('category_id'):
                warnings.append("Published posts should have a category")
        
        # Check title and content similarity
        title = item.get('title', '').lower()
        content = item.get('content', '').lower()
        
        if title and content:
            if title == content[:len(title)]:
                warnings.append("Title and content start with the same text")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

class UserValidator(BulkValidator):
    """Validator for user data"""
    
    def __init__(self):
        super().__init__()
        
        # Required fields
        self.add_required_field('username')
        self.add_required_field('email')
        
        # Optional fields
        self.add_optional_field('password')
        self.add_optional_field('first_name')
        self.add_optional_field('last_name')
        self.add_optional_field('role')
        self.add_optional_field('is_active')
        
        # Field validators
        self.add_field_validator('username', self._validate_username)
        self.add_field_validator('email', self._validate_email)
        self.add_field_validator('password', self._validate_password)
        self.add_field_validator('first_name', self._validate_name)
        self.add_field_validator('last_name', self._validate_name)
        self.add_field_validator('role', self._validate_role)
        self.add_field_validator('is_active', self._validate_boolean)
        
        # Custom validators
        self.add_custom_validator(self._validate_user_consistency)
    
    def _validate_username(self, username: str) -> Dict[str, Any]:
        """Validate username field"""
        errors = []
        
        if not isinstance(username, str):
            errors.append("Username must be a string")
            return {'valid': False, 'errors': errors}
        
        if len(username) < 3:
            errors.append("Username must be at least 3 characters long")
        
        if len(username) > 30:
            errors.append("Username cannot exceed 30 characters")
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append("Username can only contain letters, numbers, and underscores")
        
        # Check for reserved usernames
        reserved_usernames = ['admin', 'root', 'system', 'api', 'www']
        if username.lower() in reserved_usernames:
            errors.append(f"Username '{username}' is reserved")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_email(self, email: str) -> Dict[str, Any]:
        """Validate email field"""
        errors = []
        
        if not isinstance(email, str):
            errors.append("Email must be a string")
            return {'valid': False, 'errors': errors}
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            errors.append("Invalid email format")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_password(self, password: str) -> Dict[str, Any]:
        """Validate password field"""
        errors = []
        warnings = []
        
        if not isinstance(password, str):
            errors.append("Password must be a string")
            return {'valid': False, 'errors': errors}
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if len(password) > 128:
            warnings.append("Password is very long")
        
        # Check for password strength
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        if not (has_upper and has_lower and has_digit):
            warnings.append("Password should contain uppercase, lowercase, and digits")
        
        if not has_special:
            warnings.append("Password should contain special characters")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_name(self, name: str) -> Dict[str, Any]:
        """Validate name field (first_name or last_name)"""
        errors = []
        warnings = []
        
        if not isinstance(name, str):
            errors.append("Name must be a string")
            return {'valid': False, 'errors': errors}
        
        if len(name.strip()) < 1:
            errors.append("Name cannot be empty")
        
        if len(name) > 50:
            errors.append("Name cannot exceed 50 characters")
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z\s\-\'\.]+$', name):
            errors.append("Name contains invalid characters")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_role(self, role: str) -> Dict[str, Any]:
        """Validate role field"""
        errors = []
        
        valid_roles = ['user', 'admin', 'moderator', 'editor']
        if role not in valid_roles:
            errors.append(f"Role must be one of: {', '.join(valid_roles)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_boolean(self, value: Any) -> Dict[str, Any]:
        """Validate boolean field"""
        errors = []
        
        if not isinstance(value, bool):
            try:
                # Try to convert string to boolean
                if isinstance(value, str):
                    if value.lower() in ['true', '1', 'yes', 'on']:
                        return {'valid': True}
                    elif value.lower() in ['false', '0', 'no', 'off']:
                        return {'valid': True}
                
                errors.append("Value must be a boolean")
            except Exception:
                errors.append("Invalid boolean value")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_user_consistency(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user consistency"""
        errors = []
        warnings = []
        
        # Check if admin user has required fields
        if item.get('role') == 'admin':
            if not item.get('password'):
                errors.append("Admin users must have a password")
        
        # Check if active user has required fields
        if item.get('is_active', True):
            if not item.get('email'):
                errors.append("Active users must have an email")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

class CommentValidator(BulkValidator):
    """Validator for comment data"""
    
    def __init__(self):
        super().__init__()
        
        # Required fields
        self.add_required_field('content')
        self.add_required_field('post_id')
        self.add_required_field('author_id')
        
        # Optional fields
        self.add_optional_field('parent_id')
        self.add_optional_field('status')
        
        # Field validators
        self.add_field_validator('content', self._validate_content)
        self.add_field_validator('post_id', self._validate_id)
        self.add_field_validator('author_id', self._validate_id)
        self.add_field_validator('parent_id', self._validate_id)
        self.add_field_validator('status', self._validate_status)
        
        # Custom validators
        self.add_custom_validator(self._validate_comment_consistency)
    
    def _validate_content(self, content: str) -> Dict[str, Any]:
        """Validate comment content"""
        errors = []
        warnings = []
        
        if not isinstance(content, str):
            errors.append("Content must be a string")
            return {'valid': False, 'errors': errors}
        
        if len(content.strip()) < 1:
            errors.append("Content cannot be empty")
        
        if len(content) > 10000:
            warnings.append("Comment is very long")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_id(self, id_value: Any) -> Dict[str, Any]:
        """Validate ID field (post_id, author_id, parent_id)"""
        errors = []
        
        try:
            id_value = int(id_value)
            if id_value <= 0:
                errors.append("ID must be a positive integer")
        except (ValueError, TypeError):
            errors.append("ID must be a valid integer")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_status(self, status: str) -> Dict[str, Any]:
        """Validate status field"""
        errors = []
        
        valid_statuses = ['approved', 'pending', 'rejected', 'spam']
        if status not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_comment_consistency(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Validate comment consistency"""
        errors = []
        warnings = []
        
        # Check if parent_id is valid
        parent_id = item.get('parent_id')
        post_id = item.get('post_id')
        
        if parent_id and parent_id == post_id:
            errors.append("Comment cannot be its own parent")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

# Validator factory
def get_validator(resource_type: str) -> BulkValidator:
    """Get validator for resource type"""
    validators = {
        'posts': PostValidator(),
        'users': UserValidator(),
        'comments': CommentValidator()
    }
    
    return validators.get(resource_type, BulkValidator())

# Utility functions for common validations
def validate_required_fields(data: List[Dict[str, Any]], required_fields: List[str]) -> Dict[str, Any]:
    """Validate required fields for all items"""
    errors = []
    
    for i, item in enumerate(data):
        missing_fields = []
        for field in required_fields:
            if field not in item or item[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            errors.append({
                'row_index': i,
                'errors': [f"Missing required fields: {', '.join(missing_fields)}"],
                'data': item
            })
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def validate_email_format(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_url_format(url: str) -> bool:
    """Validate URL format"""
    import re
    pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$'
    return re.match(pattern, url) is not None

def validate_date_format(date_string: str) -> bool:
    """Validate date format"""
    try:
        datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False

def validate_json_format(json_string: str) -> bool:
    """Validate JSON format"""
    try:
        json.loads(json_string)
        return True
    except json.JSONDecodeError:
        return False
