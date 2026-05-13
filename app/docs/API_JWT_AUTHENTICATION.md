# JWT Token Authentication Implementation

## Overview

The JWT (JSON Web Token) authentication system provides stateless, secure authentication for API access with token generation, validation, refresh mechanisms, and comprehensive security features.

## 🏗️ Architecture

### Components

- **JWTService**: Core service for JWT token operations
- **Token Generation**: Secure token creation with claims
- **Token Validation**: Token verification and validation
- **Refresh Mechanism**: Token refresh without re-authentication
- **Token Blacklisting**: Secure token revocation
- **Security Features**: Best practices implementation

### Token Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   User      │───▶│   Login     │───▶│   JWT       │───▶│   API       │
│   Request   │    │   Request   │    │   Token     │    │   Request   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   User      │    │   Token     │    │   Token     │    │   Token     │
│   Auth      │    │   Generate   │    │   Validate   │    │   Verify    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## 🔧 Implementation Details

### JWTService Class

```python
class JWTService:
    """JWT Token Authentication Service"""
    
    def __init__(self, secret_key: str = None, algorithm: str = 'HS256'):
        """Initialize JWT service"""
        self.secret_key = secret_key or current_app.config.get('JWT_SECRET_KEY')
        self.algorithm = algorithm
        self.token_blacklist = set()
    
    def generate_token(self, user_id: int, username: str, 
                      roles: List[str] = None, expires_in: int = 3600,
                      additional_claims: Dict[str, Any] = None) -> str:
        """Generate JWT token"""
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
    
    def refresh_token(self, refresh_token: str) -> Optional[str]:
        """Refresh JWT token"""
    
    def revoke_token(self, token: str) -> bool:
        """Revoke JWT token"""
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
```

### Token Structure

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "user_id": 123,
    "username": "john_doe",
    "roles": ["user", "admin"],
    "permissions": ["read", "write"],
    "iat": 1647123456,
    "exp": 1647127056,
    "iss": "forum-api",
    "aud": "forum-users",
    "jti": "unique-token-id"
  }
}
```

## 🚀 Usage Examples

### Basic Token Generation

```python
from app.api.auth.jwt_auth import JWTService

# Initialize JWT service
jwt_service = JWTService()

# Generate token for user
token = jwt_service.generate_token(
    user_id=123,
    username="john_doe",
    roles=["user", "admin"],
    permissions=["read", "write"],
    expires_in=3600  # 1 hour
)

print(f"JWT Token: {token}")
```

### Token Validation

```python
# Verify token
payload = jwt_service.verify_token(token)

if payload:
    print(f"User ID: {payload['user_id']}")
    print(f"Username: {payload['username']}")
    print(f"Roles: {payload['roles']}")
    print(f"Expires: {payload['exp']}")
else:
    print("Invalid token")
```

### Token with Custom Claims

```python
# Generate token with custom claims
custom_claims = {
    "department": "engineering",
    "access_level": "senior",
    "last_login": "2024-03-12T10:30:00Z"
}

token = jwt_service.generate_token(
    user_id=123,
    username="john_doe",
    additional_claims=custom_claims
)
```

### Token Refresh

```python
# Refresh token (requires refresh token)
refresh_token = "user_refresh_token_123"
new_token = jwt_service.refresh_token(refresh_token)

if new_token:
    print("Token refreshed successfully")
else:
    print("Refresh token invalid or expired")
```

### Token Revocation

```python
# Revoke token
success = jwt_service.revoke_token(token)

if success:
    print("Token revoked successfully")
else:
    print("Token revocation failed")
```

## 🔗 API Endpoints

### Authentication Endpoints

| Endpoint | Method | Description | Protection |
|----------|--------|-------------|------------|
| `/api/auth/login` | POST | User login and token generation | None |
| `/api/auth/refresh` | POST | Refresh access token | JWT |
| `/api/auth/logout` | POST | User logout and token revocation | JWT |
| `/api/auth/verify` | GET | Verify token validity | JWT |
| `/api/auth/profile` | GET | Get user profile from token | JWT |

### Login Request/Response

```json
// POST /api/auth/login
{
  "username": "john_doe",
  "password": "secure_password"
}

// Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "refresh_token_abc123",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": 123,
    "username": "john_doe",
    "roles": ["user", "admin"]
  }
}
```

### Refresh Token Request/Response

```json
// POST /api/auth/refresh
{
  "refresh_token": "refresh_token_abc123"
}

// Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

## 🔐 Security Features

### Token Blacklisting

```python
# Blacklist token
jwt_service.revoke_token(token)

# Check if token is blacklisted
if jwt_service.is_token_blacklisted(token):
    print("Token is blacklisted")
```

### Token Validation with Security Checks

```python
def validate_token_with_security(token: str) -> Optional[Dict[str, Any]]:
    """Validate token with additional security checks"""
    
    # Check if token is blacklisted
    if jwt_service.is_token_blacklisted(token):
        return None
    
    # Verify token
    payload = jwt_service.verify_token(token)
    if not payload:
        return None
    
    # Check token expiration
    if payload['exp'] < time.time():
        return None
    
    # Check issuer
    if payload.get('iss') != 'forum-api':
        return None
    
    # Check audience
    if payload.get('aud') != 'forum-users':
        return None
    
    return payload
```

### Rate Limiting for Authentication

```python
from functools import wraps
from flask import request, jsonify

def rate_limit_auth(max_requests: int = 5, window: int = 300):
    """Rate limiting decorator for auth endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Implement rate limiting logic
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Apply to login endpoint
@app.route('/api/auth/login', methods=['POST'])
@rate_limit_auth(max_requests=5, window=300)
def login():
    # Login logic
    pass
```

## 📊 Token Analytics

### Token Usage Tracking

```python
class TokenAnalytics:
    """Token usage analytics"""
    
    def track_token_usage(self, token: str, endpoint: str, user_id: int):
        """Track token usage"""
        # Store usage data
        pass
    
    def get_token_stats(self, user_id: int) -> Dict[str, Any]:
        """Get token statistics for user"""
        return {
            "total_tokens": 10,
            "active_tokens": 3,
            "expired_tokens": 5,
            "revoked_tokens": 2,
            "last_activity": "2024-03-12T10:30:00Z"
        }
```

### Security Monitoring

```python
class SecurityMonitor:
    """Security monitoring for JWT tokens"""
    
    def detect_suspicious_activity(self, token: str) -> bool:
        """Detect suspicious token activity"""
        # Check for unusual patterns
        # Multiple failed validation attempts
        # Token usage from multiple locations
        # Rapid token refresh attempts
        return False
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security events"""
        pass
```

## 🔧 Configuration

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-at-least-32-characters
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES_IN=3600
JWT_REFRESH_TOKEN_EXPIRES_IN=2592000
JWT_ISSUER=forum-api
JWT_AUDIENCE=forum-users
```

### Flask Configuration

```python
# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
app.config['JWT_ALGORITHM'] = 'HS256'
app.config['JWT_ACCESS_TOKEN_EXPIRES_IN'] = 3600
app.config['JWT_REFRESH_TOKEN_EXPIRES_IN'] = 2592000
app.config['JWT_ISSUER'] = 'forum-api'
app.config['JWT_AUDIENCE'] = 'forum-users'
```

### Token Configuration

```python
# Token settings
TOKEN_SETTINGS = {
    'algorithm': 'HS256',
    'access_token_expires': 3600,  # 1 hour
    'refresh_token_expires': 2592000,  # 30 days
    'issuer': 'forum-api',
    'audience': 'forum-users',
    'leeway': 10,  # 10 seconds clock skew
    'verify_exp': True,
    'verify_iat': True,
    'verify_nbf': True
}
```

## 🛡️ Security Best Practices

### Secret Key Management

```python
import secrets
import os

# Generate secure secret key
def generate_jwt_secret():
    """Generate secure JWT secret key"""
    return secrets.token_urlsafe(32)

# Store secret key securely
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable is required")
```

### Token Claims Best Practices

```python
def create_secure_token(user_id: int, username: str) -> str:
    """Create secure JWT token with best practices"""
    
    # Use short expiration for access tokens
    expires_in = 3600  # 1 hour
    
    # Include minimal claims
    claims = {
        'user_id': user_id,
        'username': username,
        'roles': get_user_roles(user_id),
        'permissions': get_user_permissions(user_id),
        'iat': int(time.time()),
        'exp': int(time.time()) + expires_in,
        'iss': 'forum-api',
        'aud': 'forum-users',
        'jti': secrets.token_urlsafe(16)  # Unique token ID
    }
    
    return jwt.encode(claims, JWT_SECRET_KEY, algorithm='HS256')
```

### Token Validation Best Practices

```python
def validate_token_securely(token: str) -> Optional[Dict[str, Any]]:
    """Validate token with comprehensive security checks"""
    
    try:
        # Decode with all verifications
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=['HS256'],
            issuer='forum-api',
            audience='forum-users',
            options={
                'verify_exp': True,
                'verify_iat': True,
                'verify_nbf': True,
                'verify_iss': True,
                'verify_aud': True,
                'require_exp': True,
                'require_iat': True,
                'require_nbf': False
            }
        )
        
        # Additional security checks
        if not is_token_format_valid(token):
            return None
        
        if is_token_blacklisted(payload.get('jti')):
            return None
        
        return payload
        
    except jwt.ExpiredSignatureError:
        # Token expired
        return None
    except jwt.InvalidTokenError:
        # Token invalid
        return None
    except Exception:
        # Unexpected error
        return None
```

## 🧪 Testing

### Unit Tests

```python
import pytest
import jwt
from app.api.auth.jwt_auth import JWTService

class TestJWTService:
    
    def setup_method(self):
        """Setup test environment"""
        self.jwt_service = JWTService("test-secret-key")
    
    def test_token_generation(self):
        """Test token generation"""
        token = self.jwt_service.generate_token(
            user_id=1,
            username="testuser"
        )
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token structure
        decoded = jwt.decode(token, "test-secret-key", algorithms=['HS256'])
        assert decoded['user_id'] == 1
        assert decoded['username'] == "testuser"
    
    def test_token_validation(self):
        """Test token validation"""
        token = self.jwt_service.generate_token(
            user_id=1,
            username="testuser"
        )
        
        payload = self.jwt_service.verify_token(token)
        
        assert payload is not None
        assert payload['user_id'] == 1
        assert payload['username'] == "testuser"
    
    def test_token_expiration(self):
        """Test token expiration"""
        token = self.jwt_service.generate_token(
            user_id=1,
            username="testuser",
            expires_in=1  # 1 second
        )
        
        # Wait for token to expire
        import time
        time.sleep(2)
        
        payload = self.jwt_service.verify_token(token)
        assert payload is None  # Should be None for expired token
    
    def test_token_revocation(self):
        """Test token revocation"""
        token = self.jwt_service.generate_token(
            user_id=1,
            username="testuser"
        )
        
        # Revoke token
        success = self.jwt_service.revoke_token(token)
        assert success is True
        
        # Try to verify revoked token
        payload = self.jwt_service.verify_token(token)
        assert payload is None  # Should be None for revoked token
```

### Integration Tests

```python
def test_jwt_authentication_flow(client):
    """Test complete JWT authentication flow"""
    
    # Login request
    login_data = {
        "username": "testuser",
        "password": "testpassword"
    }
    
    response = client.post('/api/auth/login', json=login_data)
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'access_token' in data
    assert 'refresh_token' in data
    
    access_token = data['access_token']
    
    # Use token to access protected endpoint
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/api/auth/profile', headers=headers)
    assert response.status_code == 200
    
    # Verify token
    response = client.get('/api/auth/verify', headers=headers)
    assert response.status_code == 200
    
    # Logout (revoke token)
    response = client.post('/api/auth/logout', headers=headers)
    assert response.status_code == 200
    
    # Token should no longer be valid
    response = client.get('/api/auth/profile', headers=headers)
    assert response.status_code == 401
```

## 🔍 Troubleshooting

### Common Issues

1. **Token Invalid Signature**
   - Check JWT_SECRET_KEY configuration
   - Ensure secret key is consistent across services
   - Verify algorithm matches token encoding

2. **Token Expired**
   - Check expiration time in token payload
   - Verify system clock synchronization
   - Use refresh token to get new access token

3. **Token Blacklisted**
   - Check if token was explicitly revoked
   - Verify blacklist storage is working
   - Clear blacklist if needed for testing

4. **Invalid Claims**
   - Verify required claims are present
   - Check claim data types and formats
   - Validate custom claims structure

### Debug Logging

```python
import logging

# Enable JWT debug logging
logging.getLogger('app.api.auth.jwt_auth').setLevel(logging.DEBUG)

# Log token operations
logger = logging.getLogger('app.api.auth.jwt_auth')

def log_token_operation(operation: str, token: str, user_id: int = None):
    """Log token operations for debugging"""
    logger.debug(f"JWT {operation}: user_id={user_id}, token={token[:20]}...")
```

## 📚 References

- [JWT RFC 7519](https://tools.ietf.org/html/rfc7519)
- [JWT Security Best Practices](https://auth0.com/blog/json-web-token-best-practices)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)

---

**Last Updated**: May 12, 2026  
**Version**: 1.0.0  
**Component**: JWT Authentication Service
