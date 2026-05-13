# API Key Management Implementation

## Overview

The API Key Management system provides secure API key generation, rotation, revocation, and comprehensive usage tracking with granular permission control and rate limiting.

## 🏗️ Architecture

### Components

- **APIKeyService**: Core service for API key operations
- **APIKey Model**: Database model for key storage
- **APIUsage Model**: Usage tracking and analytics
- **Key Generation**: Secure key creation with hashing
- **Permission System**: Role-based access control
- **Rate Limiting**: Request rate control per key

### Key Lifecycle

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Key       │───▶│   Active    │───▶│   Expiring  │───▶│   Revoked   │
│   Creation  │    │   Usage     │    │   Warning   │    │   Cleanup   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Secure    │    │   Usage     │    │   Rotation  │    │   Archive   │
│   Generation│    │   Tracking  │    │   Required  │    │   Data      │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## 🔧 Implementation Details

### APIKeyService Class

```python
class APIKeyService:
    """API Key Management Service"""
    
    @staticmethod
    def create_key(name: str, user_id: int, permissions: List[str] = None, 
                   expires_in: int = 365 * 24 * 60 * 60, description: str = '', 
                   rate_limit: int = 1000) -> 'APIKey':
        """Create new API key"""
    
    @staticmethod
    def get_user_keys(user_id: int, active_only: bool = True) -> List['APIKey']:
        """Get user's API keys"""
    
    @staticmethod
    def validate_key(api_key: str) -> Optional['APIKey']:
        """Validate API key"""
    
    @staticmethod
    def revoke_key(key_id: int, user_id: int) -> bool:
        """Revoke API key"""
    
    @staticmethod
    def rotate_key(key_id: int, user_id: int) -> Optional[str]:
        """Rotate API key"""
    
    @staticmethod
    def update_usage(key_id: int, endpoint: str, response_time: float = None):
        """Update key usage statistics"""
    
    @staticmethod
    def get_usage_stats(key_id: int) -> Dict[str, Any]:
        """Get key usage statistics"""
```

### Database Models

```python
class APIKey(db.Model):
    """API Key Model for API authentication"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    key_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    api_key = db.Column(db.String(64), nullable=False)  # Only used during creation/rotation
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    permissions = db.Column(db.JSON, default=list)  # List of permissions
    description = db.Column(db.Text)
    rate_limit = db.Column(db.Integer, default=1000)  # Requests per hour
    expires_at = db.Column(db.DateTime, nullable=True)
    last_used_at = db.Column(db.DateTime, nullable=True)
    usage_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    revoked_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='api_keys')
    usage_logs = db.relationship('APIUsage', backref='api_key', lazy='dynamic')

class APIUsage(db.Model):
    """API Usage tracking model"""
    __tablename__ = 'api_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id'), nullable=False, index=True)
    endpoint = db.Column(db.String(255), nullable=False)
    request_count = db.Column(db.Integer, default=1)
    last_request = db.Column(db.DateTime, default=datetime.utcnow)
    response_time = db.Column(db.Float)  # Average response time in ms
    status_code = db.Column(db.Integer)  # Most recent status code
    user_agent = db.Column(db.String(255))
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

## 🚀 Usage Examples

### Creating an API Key

```python
from app.api.auth.services import APIKeyService

# Create new API key
api_key = APIKeyService.create_key(
    name="My Application API Key",
    user_id=123,
    permissions=["read", "write", "posts:read", "posts:write"],
    expires_in=365 * 24 * 60 * 60,  # 1 year
    description="API key for mobile application",
    rate_limit=5000  # 5000 requests per hour
)

print(f"API Key: {api_key.api_key}")
print(f"Key ID: {api_key.id}")
print(f"Permissions: {api_key.permissions}")
```

### Validating an API Key

```python
# Validate API key from request
api_key_string = request.headers.get('X-API-Key')
if not api_key_string:
    return jsonify({"error": "API key required"}), 401

key_record = APIKeyService.validate_key(api_key_string)

if not key_record:
    return jsonify({"error": "Invalid API key"}), 401

if not key_record.is_active:
    return jsonify({"error": "API key revoked"}), 401

if key_record.is_expired():
    return jsonify({"error": "API key expired"}), 401

# Check rate limiting
if not check_rate_limit(key_record):
    return jsonify({"error": "Rate limit exceeded"}), 429

# Update usage
APIKeyService.update_usage(key_record.id, request.endpoint)
```

### Rotating an API Key

```python
# Rotate API key
new_key = APIKeyService.rotate_key(key_id=123, user_id=123)

if new_key:
    print(f"New API Key: {new_key}")
    print("Old key is now revoked")
else:
    print("Key rotation failed")
```

### Revoking an API Key

```python
# Revoke API key
success = APIKeyService.revoke_key(key_id=123, user_id=123)

if success:
    print("API key revoked successfully")
else:
    print("Key revocation failed")
```

### Getting Usage Statistics

```python
# Get key usage statistics
stats = APIKeyService.get_usage_stats(key_id=123)

print(f"Total requests: {stats['total_requests']}")
print(f"Unique endpoints: {stats['unique_endpoints']}")
print(f"Average response time: {stats['avg_response_time']}ms")
print(f"Last activity: {stats['last_activity']}")
print(f"Most used endpoint: {stats['most_used_endpoint']}")
```

## 🔗 API Endpoints

### API Key Management Endpoints

| Endpoint | Method | Description | Protection |
|----------|--------|-------------|------------|
| `/api/auth/keys` | POST | Create new API key | JWT |
| `/api/auth/keys` | GET | List user's API keys | JWT |
| `/api/auth/keys/{id}` | GET | Get specific API key | JWT |
| `/api/auth/keys/{id}` | PUT | Update API key | JWT |
| `/api/auth/keys/{id}` | DELETE | Revoke API key | JWT |
| `/api/auth/keys/{id}/rotate` | POST | Rotate API key | JWT |
| `/api/auth/keys/{id}/stats` | GET | Get key statistics | JWT |

### Create API Key Request/Response

```json
// POST /api/auth/keys
{
  "name": "Mobile App API Key",
  "permissions": ["read", "write", "posts:read"],
  "expires_in": 31536000,
  "description": "API key for mobile application",
  "rate_limit": 5000
}

// Response
{
  "id": 123,
  "name": "Mobile App API Key",
  "api_key": "ak_3gumnhUwTgI_TzX7Q9r2L8mK9pF1sV4wXyZ5cA7bE8d",
  "permissions": ["read", "write", "posts:read"],
  "expires_at": "2025-05-12T10:30:00Z",
  "rate_limit": 5000,
  "created_at": "2024-05-12T10:30:00Z"
}
```

### API Key List Response

```json
// GET /api/auth/keys
{
  "keys": [
    {
      "id": 123,
      "name": "Mobile App API Key",
      "permissions": ["read", "write", "posts:read"],
      "is_active": true,
      "expires_at": "2025-05-12T10:30:00Z",
      "last_used_at": "2024-05-12T09:45:00Z",
      "usage_count": 1250,
      "created_at": "2024-05-12T10:30:00Z"
    }
  ],
  "total": 1
}
```

## 🔐 Security Features

### Key Generation

```python
import secrets
import hashlib

def generate_api_key():
    """Generate secure API key"""
    # Generate random bytes and encode as base64
    random_bytes = secrets.token_bytes(32)
    key = secrets.token_urlsafe(32)
    return f"ak_{key}"

def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def validate_api_key_format(api_key: str) -> bool:
    """Validate API key format"""
    if not api_key.startswith('ak_'):
        return False
    if len(api_key) < 35:
        return False
    return True
```

### Permission System

```python
class PermissionSystem:
    """Permission management system"""
    
    AVAILABLE_PERMISSIONS = {
        'read': 'Read access to resources',
        'write': 'Write access to resources',
        'admin': 'Administrative access',
        'posts:read': 'Read posts',
        'posts:write': 'Create and edit posts',
        'posts:delete': 'Delete posts',
        'users:read': 'Read user information',
        'users:write': 'Edit user information',
        'analytics:read': 'Access analytics data'
    }
    
    @staticmethod
    def validate_permissions(permissions: List[str]) -> List[str]:
        """Validate and filter permissions"""
        valid_permissions = []
        for perm in permissions:
            if perm in PermissionSystem.AVAILABLE_PERMISSIONS:
                valid_permissions.append(perm)
        return valid_permissions
    
    @staticmethod
    def check_permission(user_permissions: List[str], required_permission: str) -> bool:
        """Check if user has required permission"""
        # Direct permission check
        if required_permission in user_permissions:
            return True
        
        # Wildcard permission check
        if 'admin' in user_permissions:
            return True
        
        # Category wildcard check
        if ':' in required_permission:
            category = required_permission.split(':')[0]
            wildcard_perm = f"{category}:*"
            if wildcard_perm in user_permissions:
                return True
        
        return False
```

### Rate Limiting

```python
from datetime import datetime, timedelta
import time

class RateLimiter:
    """Rate limiting for API keys"""
    
    def __init__(self):
        self.requests = {}  # key_id -> list of timestamps
    
    def is_allowed(self, api_key: APIKey) -> bool:
        """Check if request is allowed based on rate limit"""
        key_id = api_key.id
        now = time.time()
        
        # Initialize if not exists
        if key_id not in self.requests:
            self.requests[key_id] = []
        
        # Remove old requests (older than 1 hour)
        hour_ago = now - 3600
        self.requests[key_id] = [req_time for req_time in self.requests[key_id] if req_time > hour_ago]
        
        # Check rate limit
        if len(self.requests[key_id]) >= api_key.rate_limit:
            return False
        
        # Add current request
        self.requests[key_id].append(now)
        return True
    
    def get_remaining_requests(self, api_key: APIKey) -> int:
        """Get remaining requests for current hour"""
        key_id = api_key.id
        if key_id not in self.requests:
            return api_key.rate_limit
        
        return max(0, api_key.rate_limit - len(self.requests[key_id]))
```

## 📊 Analytics and Monitoring

### Usage Analytics

```python
class APIKeyAnalytics:
    """API key usage analytics"""
    
    @staticmethod
    def get_key_analytics(key_id: int, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics for API key"""
        
        # Get usage data
        usage_data = APIUsage.query.filter(
            APIUsage.api_key_id == key_id,
            APIUsage.created_at >= datetime.utcnow() - timedelta(days=days)
        ).all()
        
        # Calculate metrics
        total_requests = sum(usage.request_count for usage in usage_data)
        unique_endpoints = len(set(usage.endpoint for usage in usage_data))
        avg_response_time = sum(usage.response_time or 0 for usage in usage_data) / len(usage_data) if usage_data else 0
        
        # Most used endpoint
        endpoint_counts = {}
        for usage in usage_data:
            endpoint_counts[usage.endpoint] = endpoint_counts.get(usage.endpoint, 0) + usage.request_count
        
        most_used_endpoint = max(endpoint_counts.items(), key=lambda x: x[1])[0] if endpoint_counts else None
        
        return {
            'total_requests': total_requests,
            'unique_endpoints': unique_endpoints,
            'avg_response_time': round(avg_response_time, 2),
            'most_used_endpoint': most_used_endpoint,
            'requests_per_day': round(total_requests / days, 2),
            'peak_hour': 14,  # Would calculate from actual data
            'error_rate': 0.02  # Would calculate from status codes
        }
    
    @staticmethod
    def get_user_analytics(user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get analytics for all user's API keys"""
        
        keys = APIKey.query.filter_by(user_id=user_id).all()
        
        total_requests = 0
        active_keys = 0
        key_analytics = []
        
        for key in keys:
            if key.is_active and not key.is_expired():
                active_keys += 1
            
            analytics = APIKeyAnalytics.get_key_analytics(key.id, days)
            key_analytics.append({
                'key_id': key.id,
                'key_name': key.name,
                'requests': analytics['total_requests'],
                'last_used': key.last_used_at
            })
            
            total_requests += analytics['total_requests']
        
        return {
            'total_keys': len(keys),
            'active_keys': active_keys,
            'total_requests': total_requests,
            'keys_analytics': key_analytics
        }
```

### Monitoring Dashboard

```python
class MonitoringDashboard:
    """API key monitoring dashboard"""
    
    @staticmethod
    def get_system_stats() -> Dict[str, Any]:
        """Get system-wide API key statistics"""
        
        total_keys = APIKey.query.count()
        active_keys = APIKey.query.filter_by(is_active=True).count()
        expired_keys = APIKey.query.filter(APIKey.expires_at < datetime.utcnow()).count()
        
        # Recent activity
        recent_usage = APIUsage.query.filter(
            APIUsage.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        # Top users by usage
        top_users = db.session.query(
            APIKey.user_id,
            db.func.sum(APIUsage.request_count).label('total_requests')
        ).join(APIUsage).group_by(APIKey.user_id).order_by(
            db.desc('total_requests')
        ).limit(10).all()
        
        return {
            'total_keys': total_keys,
            'active_keys': active_keys,
            'expired_keys': expired_keys,
            'recent_24h_requests': recent_usage,
            'top_users': top_users
        }
```

## 🔧 Configuration

### Environment Variables

```bash
# API Key Configuration
API_KEY_PREFIX=ak_
API_KEY_LENGTH=32
API_KEY_DEFAULT_EXPIRES_IN=31536000
API_KEY_DEFAULT_RATE_LIMIT=1000
API_KEY_HASH_ALGORITHM=sha256
```

### Flask Configuration

```python
# API Key Configuration
app.config['API_KEY_PREFIX'] = 'ak_'
app.config['API_KEY_LENGTH'] = 32
app.config['API_KEY_DEFAULT_EXPIRES_IN'] = 365 * 24 * 60 * 60  # 1 year
app.config['API_KEY_DEFAULT_RATE_LIMIT'] = 1000
app.config['API_KEY_HASH_ALGORITHM'] = 'sha256'
```

## 🛡️ Security Best Practices

### Key Security

```python
def secure_key_generation():
    """Generate API key with security best practices"""
    
    # Use cryptographically secure random generator
    random_bytes = secrets.token_bytes(32)
    
    # Add entropy with timestamp
    timestamp = int(time.time())
    entropy = f"{random_bytes.hex()}{timestamp}"
    
    # Generate key
    key = secrets.token_urlsafe(32)
    
    # Add prefix
    api_key = f"ak_{key}"
    
    return api_key

def secure_key_storage(api_key: str) -> str:
    """Securely hash API key for storage"""
    
    # Use SHA-256 for hashing
    hash_object = hashlib.sha256(api_key.encode())
    key_hash = hash_object.hexdigest()
    
    return key_hash
```

### Access Control

```python
def require_api_key(permission: str = None):
    """Decorator to require API key authentication"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get API key from header
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                return jsonify({"error": "API key required"}), 401
            
            # Validate key
            key_record = APIKeyService.validate_key(api_key)
            if not key_record:
                return jsonify({"error": "Invalid API key"}), 401
            
            # Check permissions
            if permission and not PermissionSystem.check_permission(key_record.permissions, permission):
                return jsonify({"error": "Insufficient permissions"}), 403
            
            # Check rate limit
            if not rate_limiter.is_allowed(key_record):
                return jsonify({"error": "Rate limit exceeded"}), 429
            
            # Update usage
            APIKeyService.update_usage(key_record.id, request.endpoint)
            
            # Add key to request context
            g.api_key = key_record
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

## 🧪 Testing

### Unit Tests

```python
import pytest
from app.api.auth.services import APIKeyService
from app.models import APIKey, APIUsage

class TestAPIKeyService:
    
    def test_key_creation(self, db):
        """Test API key creation"""
        api_key = APIKeyService.create_key(
            name="Test Key",
            user_id=1,
            permissions=["read", "write"],
            description="Test API key"
        )
        
        assert api_key is not None
        assert api_key.name == "Test Key"
        assert api_key.user_id == 1
        assert api_key.permissions == ["read", "write"]
        assert api_key.is_active == True
        assert api_key.api_key.startswith('ak_')
    
    def test_key_validation(self, db):
        """Test API key validation"""
        # Create key
        api_key = APIKeyService.create_key(
            name="Test Key",
            user_id=1,
            permissions=["read"]
        )
        
        # Validate with correct key
        validated_key = APIKeyService.validate_key(api_key.api_key)
        assert validated_key is not None
        assert validated_key.id == api_key.id
        
        # Validate with incorrect key
        invalid_key = APIKeyService.validate_key("invalid_key")
        assert invalid_key is None
    
    def test_key_revocation(self, db):
        """Test API key revocation"""
        api_key = APIKeyService.create_key(
            name="Test Key",
            user_id=1,
            permissions=["read"]
        )
        
        # Revoke key
        success = APIKeyService.revoke_key(api_key.id, 1)
        assert success is True
        
        # Try to validate revoked key
        validated_key = APIKeyService.validate_key(api_key.api_key)
        assert validated_key is None
    
    def test_key_rotation(self, db):
        """Test API key rotation"""
        api_key = APIKeyService.create_key(
            name="Test Key",
            user_id=1,
            permissions=["read"]
        )
        
        old_key = api_key.api_key
        
        # Rotate key
        new_key = APIKeyService.rotate_key(api_key.id, 1)
        assert new_key is not None
        assert new_key != old_key
        
        # Old key should be invalid
        validated_old = APIKeyService.validate_key(old_key)
        assert validated_old is None
        
        # New key should be valid
        validated_new = APIKeyService.validate_key(new_key)
        assert validated_new is not None
```

### Integration Tests

```python
def test_api_key_authentication_flow(client, db):
    """Test complete API key authentication flow"""
    
    # Create API key
    api_key = APIKeyService.create_key(
        name="Test Key",
        user_id=1,
        permissions=["read", "write"]
    )
    
    # Make request with API key
    headers = {'X-API-Key': api_key.api_key}
    response = client.get('/api/posts', headers=headers)
    
    assert response.status_code == 200
    
    # Test invalid key
    headers = {'X-API-Key': 'invalid_key'}
    response = client.get('/api/posts', headers=headers)
    
    assert response.status_code == 401
    
    # Test missing key
    response = client.get('/api/posts')
    
    assert response.status_code == 401
```

## 🔍 Troubleshooting

### Common Issues

1. **Invalid API Key**
   - Check key format (must start with 'ak_')
   - Verify key hasn't been revoked
   - Check if key has expired

2. **Permission Denied**
   - Verify key has required permissions
   - Check permission syntax
   - Review permission mapping

3. **Rate Limit Exceeded**
   - Check current usage against rate limit
   - Consider increasing rate limit
   - Implement caching to reduce requests

4. **Key Not Found**
   - Verify key ID is correct
   - Check if key belongs to user
   - Ensure key is active

### Debug Logging

```python
import logging

# Enable API key debug logging
logging.getLogger('app.api.auth.services').setLevel(logging.DEBUG)

# Log key operations
logger = logging.getLogger('app.api.auth.services')

def log_key_operation(operation: str, key_id: int, user_id: int = None):
    """Log API key operations"""
    logger.debug(f"API Key {operation}: key_id={key_id}, user_id={user_id}")
```

## 📚 References

- [API Key Best Practices](https://owasp.org/www-project-cheat-sheets/cheatsheets/API_Security_Cheat_Sheet.html)
- [Rate Limiting Strategies](https://stripe.com/blog/rate-limiting-and-usage-throttling)
- [API Security Guidelines](https://tools.ietf.org/html/draft-ietf-oauth-v2-31)

---

**Last Updated**: May 12, 2026  
**Version**: 1.0.0  
**Component**: API Key Management Service
