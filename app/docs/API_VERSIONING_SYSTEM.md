# API Versioning System Documentation

## Overview

The API Versioning System provides comprehensive version management for API endpoints with backward compatibility, deprecation policies, and version routing capabilities. This system ensures smooth evolution of the API while maintaining existing integrations.

## Architecture

### Core Components

1. **VersionManager** - Central management of API versions
2. **APIVersionMiddleware** - Request processing and version detection
3. **Version Decorators** - Endpoint versioning and feature flags
4. **Version Routes** - Version information and management endpoints

### Version Lifecycle

```
Active → Deprecated → Sunset → Removed
   ↓         ↓          ↓        ↓
Current   Warning   Final    Cleanup
```

## Features

### Version Management

- **Semantic Versioning**: v1.0, v1.1, v2.0, etc.
- **Status Tracking**: Active, Deprecated, Sunset
- **Backward Compatibility**: Automatic compatibility checking
- **Deprecation Policies**: Configurable warning periods

### Request Processing

- **Header-based Detection**: `API-Version: v1.0`
- **URL Path Detection**: `/api/v1/users`
- **Query Parameter Detection**: `?version=v1.0`
- **Default Version Fallback**: Configurable default version

### Endpoint Versioning

- **Version Decorators**: `@api_version('v1.0')`
- **Deprecation Warnings**: `@deprecated_endpoint('v2.0')`
- **Feature Flags**: `@beta_feature`, `@experimental_feature`
- **Min/Max Version**: `@min_version('v1.1')`, `@max_version('v2.0')`

## Implementation

### File Structure

```
app/api/versioning/
├── __init__.py                 # Package initialization
├── version_manager.py          # Core version management
├── version_middleware.py       # Request processing
├── version_decorators.py        # Endpoint decorators
├── version_routes.py           # Management routes
└── examples.py                 # Usage examples
```

### Version Manager

```python
from app.api.versioning import APIVersionManager

# Initialize version manager
version_manager = APIVersionManager()

# Register API version
version_manager.register_version(
    version='v1.0',
    status='active',
    deprecation_date=None,
    sunset_date=None
)

# Check compatibility
is_compatible = version_manager.is_compatible('v1.0', 'v1.1')
```

### Middleware Integration

```python
from app.api.versioning import APIVersionMiddleware

# Add middleware to Flask app
app.wsgi_app = APIVersionMiddleware(app.wsgi_app, app)
```

### Endpoint Versioning

```python
from app.api.versioning import api_version, deprecated_endpoint

@api_version('v1.0')
def get_users_v1():
    """Get users - v1.0 implementation"""
    return {'users': []}

@api_version('v2.0')
@deprecated_endpoint('v3.0', message='Use v3.0 API')
def get_users_v2():
    """Get users - v2.0 implementation"""
    return {'users': [], 'metadata': {}}

@api_version('v3.0')
def get_users_v3():
    """Get users - v3.0 implementation"""
    return {'users': [], 'metadata': {}, 'pagination': {}}
```

## API Endpoints

### Version Information

- `GET /api/versions` - List all available versions
- `GET /api/versions/{version}` - Get specific version details
- `GET /api/versions/compatibility/{v1}/{v2}` - Check version compatibility
- `GET /api/versions/deprecated` - List deprecated versions
- `GET /api/versions/sunset` - List sunset versions
- `GET /api/versions/migration/{from}/{to}` - Get migration guide

### Usage Examples

### Basic Versioning

```python
from flask import Blueprint
from app.api.versioning import api_version

users_bp = Blueprint('users', __name__)

@api_version('v1.0')
@users_bp.route('/users')
def get_users():
    return {'users': []}

@api_version('v2.0')
@users_bp.route('/users')
def get_users_v2():
    return {'users': [], 'version': 'v2.0'}
```

### Deprecation Handling

```python
from app.api.versioning import deprecated_endpoint

@api_version('v1.0')
@deprecated_endpoint('v2.0', message='Use v2.0 users endpoint')
def old_users_endpoint():
    return {'users': []}
```

### Feature Flags

```python
from app.api.versioning import beta_feature, experimental_feature

@api_version('v2.0')
@beta_feature
def new_feature():
    """Beta feature available in v2.0"""
    return {'feature': 'beta'}

@api_version('v2.1')
@experimental_feature
def experimental_api():
    """Experimental feature in v2.1"""
    return {'feature': 'experimental'}
```

## Configuration

### Version Configuration

```python
# app/config.py
API_VERSIONING_CONFIG = {
    'default_version': 'v1.0',
    'header_name': 'API-Version',
    'query_param': 'version',
    'url_prefix': '/api',
    'deprecation_warning_days': 90,
    'sunset_warning_days': 30
}
```

### Version Registration

```python
# app/api/versioning/registration.py
from app.api.versioning import APIVersionManager

version_manager = APIVersionManager()

# Register versions
version_manager.register_version('v1.0', 'active')
version_manager.register_version('v1.1', 'active')
version_manager.register_version('v2.0', 'active')
version_manager.register_version('v1.0', 'deprecated', deprecation_date='2024-06-01')
```

## Client Integration

### Version Detection

```python
import requests

# Using header
headers = {'API-Version': 'v1.0'}
response = requests.get('/api/users', headers=headers)

# Using query parameter
response = requests.get('/api/users?version=v1.0')

# Using URL path
response = requests.get('/api/v1/users')
```

### Backward Compatibility

```python
def api_call(endpoint, version='v1.0'):
    """Make API call with version support"""
    headers = {'API-Version': version}
    response = requests.get(endpoint, headers=headers)
    
    # Handle version mismatch
    if response.status_code == 410:
        # Version deprecated, get recommended version
        recommended = response.headers.get('API-Recommended-Version')
        return api_call(endpoint, recommended)
    
    return response.json()
```

## Migration Guide

### Version Upgrade Process

1. **Plan Migration**: Review breaking changes
2. **Update Code**: Use new endpoints/features
3. **Test Integration**: Verify compatibility
4. **Deploy**: Switch to new version
5. **Monitor**: Track performance and errors

### Breaking Changes

- **Endpoint Removal**: Endpoint no longer available
- **Parameter Changes**: Required/optional parameters modified
- **Response Format**: JSON structure changes
- **Authentication**: Auth requirements updated

### Compatibility Matrix

| From/To | v1.0 | v1.1 | v2.0 |
|---------|------|------|------|
| v1.0    | ✅    | ✅    | ⚠️    |
| v1.1    | ❌    | ✅    | ✅    |
| v2.0    | ❌    | ❌    | ✅    |

## Monitoring and Analytics

### Version Usage Tracking

```python
# Track version usage
version_stats = version_manager.get_usage_stats()
print(f"v1.0: {version_stats['v1.0']['requests']} requests")
print(f"v2.0: {version_stats['v2.0']['requests']} requests")
```

### Deprecation Monitoring

```python
# Monitor deprecated version usage
deprecated_versions = version_manager.get_deprecated_versions()
for version in deprecated_versions:
    usage = version_manager.get_version_usage(version)
    if usage['requests'] > 0:
        print(f"Version {version} still has {usage['requests']} requests")
```

## Best Practices

### Version Design

1. **Semantic Versioning**: Use MAJOR.MINOR.PATCH format
2. **Backward Compatibility**: Maintain compatibility within major versions
3. **Clear Deprecation**: Provide advance notice for breaking changes
4. **Documentation**: Document all changes and migration paths

### Endpoint Design

1. **Version Specific**: Create version-specific endpoints when needed
2. **Shared Logic**: Reuse common logic across versions
3. **Graceful Degradation**: Handle missing features gracefully
4. **Testing**: Test all supported versions

### Client Integration

1. **Version Detection**: Implement proper version detection
2. **Error Handling**: Handle version-related errors
3. **Fallback**: Provide fallback mechanisms
4. **Updates**: Plan for version updates

## Troubleshooting

### Common Issues

1. **Version Not Found**: Check version registration
2. **Compatibility Error**: Verify version compatibility matrix
3. **Deprecation Warning**: Update to recommended version
4. **Routing Issues**: Check middleware configuration

### Debug Mode

```python
# Enable versioning debug mode
app.config['API_VERSIONING_DEBUG'] = True

# View version detection logs
import logging
logging.getLogger('app.api.versioning').setLevel(logging.DEBUG)
```

### Version Conflicts

```python
# Resolve version conflicts
conflicts = version_manager.detect_conflicts()
if conflicts:
    print(f"Version conflicts: {conflicts}")
    # Resolve conflicts...
```

## Security Considerations

### Version Security

1. **Access Control**: Restrict access to deprecated versions
2. **Rate Limiting**: Apply different limits per version
3. **Authentication**: Maintain auth consistency across versions
4. **Audit Logging**: Log version usage and access patterns

### Deprecation Security

1. **Sunset Enforcement**: Remove sunset versions on schedule
2. **Migration Assistance**: Help users migrate from deprecated versions
3. **Communication**: Notify users of upcoming changes
4. **Fallback Protection**: Prevent fallback to insecure versions

## Performance Optimization

### Caching

```python
# Cache version information
from flask_caching import Cache

cache = Cache(app)

@cache.memoize(timeout=300)
def get_version_info(version):
    return version_manager.get_version(version)
```

### Routing Optimization

```python
# Optimize version routing
@app.before_request
def optimize_version_routing():
    version = request.headers.get('API-Version')
    if version:
        # Use cached version info
        request.version_info = get_version_info(version)
```

## Future Enhancements

### Planned Features

1. **Auto-Migration**: Automatic code migration suggestions
2. **Version Testing**: Automated compatibility testing
3. **Performance Metrics**: Per-version performance tracking
4. **Client SDKs**: Version-specific client libraries

### Extension Points

1. **Custom Detectors**: Additional version detection methods
2. **Version Policies**: Custom deprecation policies
3. **Integration Hooks**: Hooks for external systems
4. **Analytics**: Enhanced usage analytics

---

**Last Updated**: May 12, 2026  
**Version**: 1.0  
**Status**: Production Ready
