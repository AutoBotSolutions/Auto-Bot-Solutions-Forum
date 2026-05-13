# OAuth2 Authentication Implementation

## Overview

The OAuth2 authentication system provides secure, standards-based authentication for API access with support for multiple providers, client management, and granular permission control.

## 🏗️ Architecture

### Components

- **OAuth2Service**: Core service for OAuth2 operations
- **OAuth2Client**: Client application management
- **OAuth2Token**: Access and refresh token management
- **OAuth2AuthorizationCode**: Authorization code flow
- **OAuth2RefreshToken**: Refresh token management
- **OAuth2Scope**: Permission scope management
- **OAuth2UserConsent**: User consent tracking

### Flow Diagram

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│  OAuth2     │───▶│   User      │───▶│  Token      │
│ Application │    │  Service    │    │  Consent    │    │  Service    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │    │  Auth Code  │    │   Access    │    │   Refresh   │
│   ID/Secret │    │   Flow      │    │   Token     │    │   Token     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## 🔧 Implementation Details

### Service Classes

#### OAuth2Service

```python
class OAuth2Service:
    """OAuth2 Authentication Service"""
    
    @staticmethod
    def create_client(name: str, redirect_uris: List[str], scopes: List[str], 
                     user_id: Optional[int] = None, client_uri: str = '') -> OAuth2Client:
        """Create a new OAuth2 client"""
    
    @staticmethod
    def get_client_by_id(client_id: str) -> Optional[OAuth2Client]:
        """Get OAuth2 client by ID"""
    
    @staticmethod
    def create_access_token(user_id: Optional[int], client_id: str, scope: str, 
                          expires_in: int = 3600, refresh_token_enabled: bool = True) -> OAuth2Token:
        """Create access token"""
    
    @staticmethod
    def validate_access_token(access_token: str) -> Optional[OAuth2Token]:
        """Validate access token"""
```

#### Database Models

```python
class OAuth2Client(db.Model, OAuth2ClientMixin):
    """OAuth2 Client Model"""
    __tablename__ = 'oauth2_clients'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    client_id = Column(String(64), unique=True, nullable=False, index=True)
    client_secret = Column(String(128), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    redirect_uris = Column(JSON, nullable=False)
    scopes = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class OAuth2Token(db.Model, OAuth2TokenMixin):
    """OAuth2 Token Model"""
    __tablename__ = 'oauth2_tokens'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(String(64), ForeignKey('oauth2_clients.client_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    access_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    scope = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked = Column(Boolean, default=False)
```

## 🚀 Usage Examples

### Creating an OAuth2 Client

```python
from app.api.auth.services import OAuth2Service

# Create a new OAuth2 client
client = OAuth2Service.create_client(
    name="My Application",
    redirect_uris=["https://myapp.com/callback", "https://myapp.com/oauth/callback"],
    scopes=["read", "write", "profile"],
    user_id=123
)

print(f"Client ID: {client.client_id}")
print(f"Client Secret: {client.client_secret}")
```

### Authorization Code Flow

```python
# Step 1: Redirect user to authorization endpoint
authorization_url = f"/api/auth/oauth2/authorize?response_type=code&client_id={client.client_id}&redirect_uri={redirect_uri}&scope=read+write&state={state}"

# Step 2: User authorizes and receives authorization code
auth_code = "received_authorization_code"

# Step 3: Exchange code for access token
token = OAuth2Service.create_access_token(
    user_id=123,
    client_id=client.client_id,
    scope="read write",
    expires_in=3600
)

print(f"Access Token: {token.access_token}")
print(f"Refresh Token: {token.refresh_token}")
```

### Token Validation

```python
# Validate access token
token = OAuth2Service.validate_access_token(access_token)

if token and token.is_valid():
    print(f"Token valid for user: {token.user_id}")
    print(f"Token scopes: {token.scope_list}")
else:
    print("Invalid or expired token")
```

### Refresh Token Flow

```python
# Refresh access token
new_token = OAuth2Service.refresh_access_token(
    refresh_token=old_token.refresh_token,
    client_id=client.client_id
)

if new_token:
    print(f"New Access Token: {new_token.access_token}")
else:
    print("Refresh token invalid or expired")
```

## 🔗 API Endpoints

### Authorization Endpoints

| Endpoint | Method | Description | Protection |
|----------|--------|-------------|------------|
| `/api/auth/oauth2/authorize` | GET | Authorization endpoint | OAuth2 |
| `/api/auth/oauth2/callback` | GET | OAuth2 callback | OAuth2 |
| `/api/auth/oauth2/token` | POST | Token exchange | OAuth2 |
| `/api/auth/oauth2/refresh` | POST | Refresh token | OAuth2 |
| `/api/auth/oauth2/revoke` | POST | Revoke token | OAuth2 |

### Client Management Endpoints

| Endpoint | Method | Description | Protection |
|----------|--------|-------------|------------|
| `/api/auth/clients` | POST | Create client | JWT |
| `/api/auth/clients/{id}` | GET | Get client | JWT |
| `/api/auth/clients/{id}` | PUT | Update client | JWT |
| `/api/auth/clients/{id}` | DELETE | Delete client | JWT |
| `/api/auth/clients/{id}/secret` | POST | Rotate secret | JWT |

## 🔐 Security Features

### Client Secret Management

```python
# Rotate client secret
new_secret = OAuth2Service.rotate_client_secret(client_id)
print(f"New Client Secret: {new_secret}")

# Revoke client
success = OAuth2Service.revoke_client(client_id)
```

### Token Security

- **Access Tokens**: Short-lived (1 hour default)
- **Refresh Tokens**: Long-lived (30 days default)
- **Token Scopes**: Granular permission control
- **Token Blacklisting**: Immediate revocation support
- **Secure Storage**: Tokens hashed and encrypted

### Scope Management

```python
# Define available scopes
scopes = [
    "read",      # Read access to resources
    "write",     # Write access to resources
    "admin",     # Administrative access
    "profile",   # User profile access
    "email"      # Email access
]

# Validate scopes
valid_scopes = OAuth2Service.validate_scopes(["read", "write", "invalid_scope"])
# Returns: ["read", "write"]
```

## 📊 Analytics and Monitoring

### Client Statistics

```python
# Get client statistics
stats = OAuth2Service.get_client_stats(client_id)
print(f"Active tokens: {stats['active_tokens']}")
print(f"Total requests: {stats['total_requests']}")
print(f"Last activity: {stats['last_activity']}")
```

### User Statistics

```python
# Get user statistics
user_stats = OAuth2Service.get_user_stats(user_id)
print(f"Active clients: {user_stats['active_clients']}")
print(f"Active tokens: {user_stats['active_tokens']}")
```

## 🔧 Configuration

### Environment Variables

```bash
# OAuth2 Configuration
OAUTH2_GOOGLE_CLIENT_ID=your-google-client-id
OAUTH2_GOOGLE_CLIENT_SECRET=your-google-client-secret
OAUTH2_GITHUB_CLIENT_ID=your-github-client-id
OAUTH2_GITHUB_CLIENT_SECRET=your-github-client-secret

# Token Configuration
JWT_SECRET_KEY=your-jwt-secret-key
OAUTH2_ACCESS_TOKEN_EXPIRES_IN=3600
OAUTH2_REFRESH_TOKEN_EXPIRES_IN=2592000
```

### Flask Configuration

```python
# OAuth2 Configuration
app.config['OAUTH2_ACCESS_TOKEN_EXPIRES_IN'] = 3600
app.config['OAUTH2_REFRESH_TOKEN_EXPIRES_IN'] = 2592000
app.config['OAUTH2_CLIENT_SECRET_EXPIRES_IN'] = 31536000
```

## 🧪 Testing

### Unit Tests

```python
def test_oauth2_client_creation():
    client = OAuth2Service.create_client(
        name="Test Client",
        redirect_uris=["https://test.com/callback"],
        scopes=["read", "write"],
        user_id=1
    )
    
    assert client.client_id is not None
    assert client.client_secret is not None
    assert client.is_active == True

def test_token_validation():
    token = OAuth2Service.create_access_token(
        user_id=1,
        client_id="test_client",
        scope="read"
    )
    
    validated_token = OAuth2Service.validate_access_token(token.access_token)
    assert validated_token is not None
    assert validated_token.user_id == 1
```

### Integration Tests

```python
def test_oauth2_flow():
    # Create client
    client = OAuth2Service.create_client(
        name="Test App",
        redirect_uris=["https://test.com/callback"],
        scopes=["read"],
        user_id=1
    )
    
    # Create authorization code
    auth_code = OAuth2Service.create_authorization_code(
        client_id=client.client_id,
        user_id=1,
        redirect_uri="https://test.com/callback",
        scope="read"
    )
    
    # Exchange for token
    token = OAuth2Service.create_access_token(
        user_id=1,
        client_id=client.client_id,
        scope="read"
    )
    
    # Validate token
    validated_token = OAuth2Service.validate_access_token(token.access_token)
    assert validated_token is not None
```

## 🔍 Troubleshooting

### Common Issues

1. **Invalid Client Credentials**
   - Verify client ID and secret
   - Check if client is active

2. **Token Expired**
   - Use refresh token to get new access token
   - Re-authenticate if refresh token expired

3. **Invalid Scope**
   - Check requested scopes against available scopes
   - Ensure user has required permissions

4. **Redirect URI Mismatch**
   - Verify redirect URI matches registered URIs
   - Check for exact match including protocol

### Debug Logging

```python
import logging

# Enable OAuth2 debug logging
logging.getLogger('app.api.auth.oauth2').setLevel(logging.DEBUG)
```

## 📚 References

- [OAuth2 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [OAuth2 Security Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
- [Flask-OAuthlib Documentation](https://flask-oauthlib.readthedocs.io/)

---

**Last Updated**: May 12, 2026  
**Version**: 1.0.0  
**Component**: OAuth2 Authentication Service
