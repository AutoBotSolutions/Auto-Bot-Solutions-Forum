# OpenAPI/Swagger Documentation Implementation

## Overview

The OpenAPI/Swagger documentation system provides comprehensive, interactive API documentation with automatic specification generation, client code generation, and real-time API exploration capabilities.

## 🏗️ Architecture

### Components

- **OpenAPIService**: Core service for OpenAPI specification generation
- **SwaggerUIService**: Interactive API explorer interface
- **APIDocsBlueprint**: Flask blueprint for documentation endpoints
- **SpecGenerator**: Automatic specification generation from Flask routes
- **ClientCodeGenerator**: Multi-language client code generation
- **DocumentationValidator**: Specification validation and compliance

### Documentation Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Flask     │───▶│   OpenAPI   │───▶│   Swagger   │───▶│   Interactive│
│   Routes    │    │   Service   │    │   UI        │    │   Explorer   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Route     │    │   Spec      │    │   Client    │    │   Real-time  │
│   Parsing    │    │   Generation│    │   Code      │    │   Testing    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## 🔧 Implementation Details

### OpenAPIService Class

```python
class OpenAPIService:
    """OpenAPI 3.0 specification service"""
    
    def __init__(self, title: str, version: str, description: str = ""):
        """Initialize OpenAPI service"""
        self.spec = {
            "openapi": "3.0.3",
            "info": {
                "title": title,
                "version": version,
                "description": description
            },
            "servers": [],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {},
                "responses": {},
                "parameters": {}
            },
            "tags": [],
            "security": []
        }
        self.security_schemes = {}
        self.schemas = {}
        self.responses = {}
        self.parameters = {}
    
    def add_server(self, url: str, description: str = ""):
        """Add server URL to specification"""
    
    def add_tag(self, name: str, description: str = ""):
        """Add tag to specification"""
    
    def add_security_scheme(self, name: str, scheme_type: str, **kwargs):
        """Add security scheme to specification"""
    
    def add_schema(self, name: str, schema: Dict[str, Any]):
        """Add schema to specification"""
    
    def add_response(self, name: str, response: Dict[str, Any]):
        """Add response to specification"""
    
    def add_parameter(self, name: str, parameter: Dict[str, Any]):
        """Add parameter to specification"""
    
    def register_endpoint(self, path: str, methods: Dict[str, Any]):
        """Register endpoint in specification"""
    
    def get_spec(self) -> Dict[str, Any]:
        """Get complete OpenAPI specification"""
    
    def get_spec_json(self) -> str:
        """Get OpenAPI specification as JSON"""
    
    def validate_spec(self) -> Dict[str, Any]:
        """Validate OpenAPI specification"""
```

### SwaggerUIService Class

```python
class SwaggerUIService:
    """Swagger UI service for interactive documentation"""
    
    def __init__(self, openapi_service: OpenAPIService):
        """Initialize Swagger UI service"""
        self.openapi_service = openapi_service
    
    def get_swagger_html(self) -> str:
        """Get Swagger UI HTML page"""
    
    def get_config_json(self) -> str:
        """Get Swagger UI configuration"""
    
    def get_openapi_json(self) -> str:
        """Get OpenAPI specification JSON"""
    
    def get_openapi_yaml(self) -> str:
        """Get OpenAPI specification YAML"""
    
    def search_endpoints(self, query: str) -> List[Dict[str, Any]]:
        """Search endpoints by query"""
    
    def get_endpoint_details(self, path: str, method: str) -> Dict[str, Any]:
        """Get detailed endpoint information"""
    
    def generate_client_code(self, path: str, method: str, language: str = "javascript") -> str:
        """Generate client code for endpoint"""
```

## 🚀 Usage Examples

### Basic OpenAPI Setup

```python
from app.api.docs.openapi import OpenAPIService
from app.api.docs.swagger_ui import SwaggerUIService

# Initialize OpenAPI service
openapi_service = OpenAPIService(
    title="Auto Bot Solutions Forum API",
    version="1.0.0",
    description="Complete API documentation for the Auto Bot Solutions Forum"
)

# Add servers
openapi_service.add_server("http://localhost:5000", "Development Server")
openapi_service.add_server("https://api.forum.example.com", "Production Server")

# Add tags
openapi_service.add_tag("Authentication", "User authentication and authorization")
openapi_service.add_tag("Posts", "Forum post management")
openapi_service.add_tag("Users", "User management")

# Initialize Swagger UI
swagger_service = SwaggerUIService(openapi_service)
```

### Adding Security Schemes

```python
# Add API key authentication
openapi_service.add_security_scheme(
    name="ApiKeyAuth",
    scheme_type="apiKey",
    name_param="X-API-Key",
    location="header",
    description="API key for authentication"
)

# Add JWT authentication
openapi_service.add_security_scheme(
    name="JWTAuth",
    scheme_type="http",
    scheme="bearer",
    bearerFormat="JWT",
    description="JWT token for authentication"
)

# Add OAuth2 authentication
openapi_service.add_security_scheme(
    name="OAuth2",
    scheme_type="oauth2",
    flows={
        "authorizationCode": {
            "authorizationUrl": "/api/auth/oauth2/authorize",
            "tokenUrl": "/api/auth/oauth2/token",
            "scopes": {
                "read": "Read access",
                "write": "Write access",
                "admin": "Admin access"
            }
        }
    },
    description="OAuth2 authentication"
)
```

### Adding Schemas

```python
# User schema
openapi_service.add_schema("User", {
    "type": "object",
    "properties": {
        "id": {
            "type": "integer",
            "description": "User ID"
        },
        "username": {
            "type": "string",
            "description": "Username"
        },
        "email": {
            "type": "string",
            "format": "email",
            "description": "Email address"
        },
        "created_at": {
            "type": "string",
            "format": "date-time",
            "description": "Account creation date"
        }
    },
    "required": ["id", "username", "email"]
})

# Post schema
openapi_service.add_schema("Post", {
    "type": "object",
    "properties": {
        "id": {
            "type": "integer",
            "description": "Post ID"
        },
        "title": {
            "type": "string",
            "description": "Post title"
        },
        "content": {
            "type": "string",
            "description": "Post content"
        },
        "author": {
            "$ref": "#/components/schemas/User"
        },
        "created_at": {
            "type": "string",
            "format": "date-time",
            "description": "Post creation date"
        }
    },
    "required": ["id", "title", "content", "author"]
})
```

### Adding Responses

```python
# Success response
openapi_service.add_response("Success", {
    "description": "Successful operation",
    "content": {
        "application/json": {
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": True
                    },
                    "data": {
                        "type": "object"
                    },
                    "message": {
                        "type": "string",
                        "example": "Operation completed successfully"
                    }
                }
            }
        }
    }
})

# Error response
openapi_service.add_response("BadRequest", {
    "description": "Bad request",
    "content": {
        "application/json": {
            "schema": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "example": "Bad request"
                    },
                    "message": {
                        "type": "string",
                        "example": "Invalid request parameters"
                    },
                    "details": {
                        "type": "object",
                        "example": {"field": "error details"}
                    }
                }
            }
        }
    }
})

# Unauthorized response
openapi_service.add_response("Unauthorized", {
    "description": "Unauthorized access",
    "content": {
        "application/json": {
            "schema": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "example": "Unauthorized"
                    },
                    "message": {
                        "type": "string",
                        "example": "Authentication required"
                    }
                }
            }
        }
    }
})
```

### Registering Endpoints

```python
# Register post endpoints
openapi_service.register_endpoint("/api/posts", {
    "get": {
        "summary": "Get all posts",
        "description": "Retrieve a list of all forum posts",
        "tags": ["Posts"],
        "parameters": [
            {
                "name": "page",
                "in": "query",
                "description": "Page number",
                "required": False,
                "schema": {"type": "integer", "default": 1}
            },
            {
                "name": "limit",
                "in": "query",
                "description": "Number of posts per page",
                "required": False,
                "schema": {"type": "integer", "default": 20}
            }
        ],
        "responses": {
            "200": {
                "description": "List of posts",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "posts": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Post"}
                                },
                                "pagination": {
                                    "type": "object",
                                    "properties": {
                                        "page": {"type": "integer"},
                                        "limit": {"type": "integer"},
                                        "total": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "post": {
        "summary": "Create new post",
        "description": "Create a new forum post",
        "tags": ["Posts"],
        "security": [{"ApiKeyAuth": []}, {"JWTAuth": []}],
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["title", "content"]
                    }
                }
            }
        },
        "responses": {
            "201": {"$ref": "#/components/responses/Success"},
            "400": {"$ref": "#/components/responses/BadRequest"},
            "401": {"$ref": "#/components/responses/Unauthorized"}
        }
    }
})
```

## 🔗 Documentation Endpoints

### API Documentation Blueprint

```python
from flask import Blueprint, jsonify, request
from app.api.docs.openapi import OpenAPIService
from app.api.docs.swagger_ui import SwaggerUIService

api_docs_bp = Blueprint('api_docs', __name__, url_prefix='/api/docs')

@api_docs_bp.route('/')
def docs_index():
    """Documentation index page"""
    return swagger_service.get_swagger_html()

@api_docs_bp.route('/openapi.json')
def openapi_spec():
    """OpenAPI specification JSON"""
    return swagger_service.get_openapi_json(), 200, {
        'Content-Type': 'application/json'
    }

@api_docs_bp.route('/openapi.yaml')
def openapi_spec_yaml():
    """OpenAPI specification YAML"""
    return swagger_service.get_openapi_yaml(), 200, {
        'Content-Type': 'application/x-yaml'
    }

@api_docs_bp.route('/config.json')
def swagger_config():
    """Swagger UI configuration"""
    return swagger_service.get_config_json(), 200, {
        'Content-Type': 'application/json'
    }

@api_docs_bp.route('/search')
def search_endpoints():
    """Search API endpoints"""
    query = request.args.get('q', '')
    results = swagger_service.search_endpoints(query)
    return jsonify(results)

@api_docs_bp.route('/endpoint/<path:path>')
def get_endpoint_details(path):
    """Get endpoint details"""
    method = request.args.get('method', 'get')
    details = swagger_service.get_endpoint_details(path, method)
    return jsonify(details)

@api_docs_bp.route('/generate-code')
def generate_client_code():
    """Generate client code for endpoint"""
    path = request.args.get('path')
    method = request.args.get('method', 'get')
    language = request.args.get('language', 'javascript')
    
    code = swagger_service.generate_client_code(path, method, language)
    return jsonify({'code': code})
```

### Available Endpoints

| Endpoint | Method | Description | Format |
|----------|--------|-------------|--------|
| `/api/docs/` | GET | Interactive Swagger UI | HTML |
| `/api/docs/openapi.json` | GET | OpenAPI specification | JSON |
| `/api/docs/openapi.yaml` | GET | OpenAPI specification | YAML |
| `/api/docs/config.json` | GET | Swagger UI configuration | JSON |
| `/api/docs/search` | GET | Search endpoints | JSON |
| `/api/docs/endpoint/{path}` | GET | Endpoint details | JSON |
| `/api/docs/generate-code` | GET | Generate client code | JSON |

## 🎨 Swagger UI Customization

### Custom CSS

```css
/* Custom Swagger UI styling */
.swagger-ui .topbar {
    background-color: #2c3e50;
    border-bottom: 3px solid #3498db;
}

.swagger-ui .info .title {
    color: #2c3e50;
}

.swagger-ui .scheme-container {
    background: #ecf0f1;
    border: 1px solid #bdc3c7;
}

.swagger-ui .opblock.opblock-post {
    border-color: #27ae60;
    background: rgba(39, 174, 96, 0.1);
}

.swagger-ui .opblock.opblock-get {
    border-color: #3498db;
    background: rgba(52, 152, 219, 0.1);
}

.swagger-ui .opblock.opblock-delete {
    border-color: #e74c3c;
    background: rgba(231, 76, 60, 0.1);
}
```

### Custom Configuration

```python
def get_swagger_config():
    """Get custom Swagger UI configuration"""
    return {
        "url": "/api/docs/openapi.json",
        "dom_id": "#swagger-ui",
        "deepLinking": True,
        "presets": [
            SwaggerUIBundle.presets.apis,
            SwaggerUIStandalonePreset
        ],
        "plugins": [
            SwaggerUIBundle.plugins.DownloadUrl
        ],
        "layout": "StandaloneLayout",
        "defaultModelsExpandDepth": 1,
        "defaultModelExpandDepth": 1,
        "defaultModelRendering": "example",
        "displayRequestDuration": True,
        "docExpansion": "none",
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "tryItOutEnabled": True,
        "requestInterceptor": """
            function(request) {
                // Add custom headers
                request.headers['X-Custom-Header'] = 'CustomValue';
                return request;
            }
        """,
        "responseInterceptor": """
            function(response) {
                // Log responses
                console.log('Response:', response);
                return response;
            }
        """
    }
```

## 🔧 Client Code Generation

### JavaScript Client Code

```javascript
// Generated JavaScript client code
async function getPosts(page = 1, limit = 20) {
    const url = `/api/posts?page=${page}&limit=${limit}`;
    
    const options = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            // Add your authentication headers here
            'X-API-Key': 'your-api-key'
        }
    };
    
    try {
        const response = await fetch(url, options);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Example usage:
// getPosts(1, 20).then(data => console.log(data));
```

### Python Client Code

```python
# Generated Python client code
import requests
import json

def get_posts(page=1, limit=20):
    """
    Get all posts
    """
    url = f"/api/posts"
    
    params = {
        'page': page,
        'limit': limit
    }
    
    headers = {
        'Content-Type': 'application/json',
        # Add your authentication headers here
        'X-API-Key': 'your-api-key'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API call failed: {e}")
        raise

# Example usage:
# posts = get_posts(1, 20)
# print(posts)
```

### cURL Client Code

```bash
# Generated cURL client code
curl -X GET "https://api.forum.example.com/api/posts?page=1&limit=20" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -H "Accept: application/json"
```

## 📊 Documentation Analytics

### Usage Tracking

```python
class DocumentationAnalytics:
    """Documentation usage analytics"""
    
    def __init__(self):
        self.page_views = {}
        self.endpoint_views = {}
        self.code_generations = {}
    
    def track_page_view(self, page: str, user_agent: str = None):
        """Track documentation page view"""
        timestamp = datetime.utcnow().isoformat()
        
        if page not in self.page_views:
            self.page_views[page] = []
        
        self.page_views[page].append({
            'timestamp': timestamp,
            'user_agent': user_agent
        })
    
    def track_endpoint_view(self, path: str, method: str):
        """Track endpoint documentation view"""
        key = f"{method.upper()} {path}"
        
        if key not in self.endpoint_views:
            self.endpoint_views[key] = 0
        
        self.endpoint_views[key] += 1
    
    def track_code_generation(self, path: str, method: str, language: str):
        """Track client code generation"""
        key = f"{language}:{method.upper()} {path}"
        
        if key not in self.code_generations:
            self.code_generations[key] = 0
        
        self.code_generations[key] += 1
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary"""
        return {
            'total_page_views': sum(len(views) for views in self.page_views.values()),
            'popular_pages': sorted(
                [(page, len(views)) for page, views in self.page_views.items()],
                key=lambda x: x[1], reverse=True
            )[:10],
            'popular_endpoints': sorted(
                self.endpoint_views.items(),
                key=lambda x: x[1], reverse=True
            )[:10],
            'popular_code_generations': sorted(
                self.code_generations.items(),
                key=lambda x: x[1], reverse=True
            )[:10]
        }
```

## 🔍 Specification Validation

### OpenAPI Validation

```python
class OpenAPIValidator:
    """OpenAPI specification validation"""
    
    def __init__(self, spec: Dict[str, Any]):
        self.spec = spec
        self.errors = []
        self.warnings = []
    
    def validate(self) -> Dict[str, Any]:
        """Validate OpenAPI specification"""
        
        # Validate required fields
        self._validate_required_fields()
        
        # Validate info section
        self._validate_info()
        
        # Validate paths
        self._validate_paths()
        
        # Validate components
        self._validate_components()
        
        # Validate security
        self._validate_security()
        
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings
        }
    
    def _validate_required_fields(self):
        """Validate required OpenAPI fields"""
        required_fields = ['openapi', 'info', 'paths']
        
        for field in required_fields:
            if field not in self.spec:
                self.errors.append(f"Missing required field: {field}")
    
    def _validate_info(self):
        """Validate info section"""
        info = self.spec.get('info', {})
        
        if 'title' not in info:
            self.errors.append("Missing required field: info.title")
        
        if 'version' not in info:
            self.errors.append("Missing required field: info.version")
    
    def _validate_paths(self):
        """Validate paths section"""
        paths = self.spec.get('paths', {})
        
        for path, path_item in paths.items():
            if not path.startswith('/'):
                self.warnings.append(f"Path should start with '/': {path}")
            
            for method, operation in path_item.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    self._validate_operation(path, method, operation)
    
    def _validate_operation(self, path: str, method: str, operation: Dict[str, Any]):
        """Validate individual operation"""
        
        if 'responses' not in operation:
            self.errors.append(f"Missing responses for {method.upper()} {path}")
        
        if 'summary' not in operation:
            self.warnings.append(f"Missing summary for {method.upper()} {path}")
        
        # Validate parameters
        parameters = operation.get('parameters', [])
        for param in parameters:
            if 'name' not in param:
                self.errors.append(f"Parameter missing name in {method.upper()} {path}")
            
            if 'in' not in param:
                self.errors.append(f"Parameter missing location in {method.upper()} {path}")
```

## 🧪 Testing

### Unit Tests

```python
import pytest
from app.api.docs.openapi import OpenAPIService

class TestOpenAPIService:
    
    def test_initialization(self):
        """Test OpenAPI service initialization"""
        service = OpenAPIService(
            title="Test API",
            version="1.0.0",
            description="Test API description"
        )
        
        spec = service.get_spec()
        
        assert spec['openapi'] == '3.0.3'
        assert spec['info']['title'] == 'Test API'
        assert spec['info']['version'] == '1.0.0'
        assert spec['info']['description'] == 'Test API description'
    
    def test_add_server(self):
        """Test adding server URL"""
        service = OpenAPIService("Test API", "1.0.0")
        service.add_server("http://localhost:5000", "Development Server")
        
        spec = service.get_spec()
        servers = spec['servers']
        
        assert len(servers) == 1
        assert servers[0]['url'] == 'http://localhost:5000'
        assert servers[0]['description'] == 'Development Server'
    
    def test_add_security_scheme(self):
        """Test adding security scheme"""
        service = OpenAPIService("Test API", "1.0.0")
        service.add_security_scheme(
            name="ApiKeyAuth",
            scheme_type="apiKey",
            name_param="X-API-Key",
            location="header"
        )
        
        spec = service.get_spec()
        security_schemes = spec['components']['securitySchemes']
        
        assert 'ApiKeyAuth' in security_schemes
        assert security_schemes['ApiKeyAuth']['type'] == 'apiKey'
        assert security_schemes['ApiKeyAuth']['name'] == 'X-API-Key'
        assert security_schemes['ApiKeyAuth']['in'] == 'header'
    
    def test_add_schema(self):
        """Test adding schema"""
        service = OpenAPIService("Test API", "1.0.0")
        
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"}
            }
        }
        
        service.add_schema("TestModel", schema)
        
        spec = service.get_spec()
        schemas = spec['components']['schemas']
        
        assert 'TestModel' in schemas
        assert schemas['TestModel']['type'] == 'object'
        assert 'id' in schemas['TestModel']['properties']
        assert 'name' in schemas['TestModel']['properties']
    
    def test_register_endpoint(self):
        """Test endpoint registration"""
        service = OpenAPIService("Test API", "1.0.0")
        
        endpoint = {
            "get": {
                "summary": "Get test resource",
                "responses": {
                    "200": {
                        "description": "Success",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    }
                }
            }
        }
        
        service.register_endpoint("/test", endpoint)
        
        spec = service.get_spec()
        paths = spec['paths']
        
        assert '/test' in paths
        assert 'get' in paths['/test']
        assert paths['/test']['get']['summary'] == 'Get test resource'
```

### Integration Tests

```python
def test_openapi_endpoint(client, openapi_service):
    """Test OpenAPI specification endpoint"""
    
    response = client.get('/api/docs/openapi.json')
    
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    
    data = response.get_json()
    assert 'openapi' in data
    assert 'info' in data
    assert 'paths' in data
    assert 'components' in data

def test_swagger_ui_endpoint(client):
    """Test Swagger UI endpoint"""
    
    response = client.get('/api/docs/')
    
    assert response.status_code == 200
    assert 'text/html' in response.content_type
    assert 'swagger-ui' in response.get_data(as_text=True).lower()

def test_endpoint_search(client, swagger_service):
    """Test endpoint search functionality"""
    
    response = client.get('/api/docs/search?q=posts')
    
    assert response.status_code == 200
    data = response.get_json()
    
    assert isinstance(data, list)
    # Should return endpoints related to posts
```

## 🔍 Troubleshooting

### Common Issues

1. **Specification Not Loading**
   - Check OpenAPI service initialization
   - Verify Flask blueprint registration
   - Check for syntax errors in specification

2. **Swagger UI Not Displaying**
   - Verify static files are accessible
   - Check JavaScript console for errors
   - Ensure OpenAPI JSON is valid

3. **Endpoints Not Registered**
   - Check Flask route registration
   - Verify endpoint registration in OpenAPI service
   - Check for naming conflicts

4. **Client Code Generation Issues**
   - Verify endpoint details are complete
   - Check for missing parameters
   - Validate HTTP method specifications

### Debug Tools

```python
def debug_openapi_spec(openapi_service: OpenAPIService):
    """Debug OpenAPI specification issues"""
    
    spec = openapi_service.get_spec()
    
    print("=== OpenAPI Specification Debug ===")
    print(f"OpenAPI Version: {spec.get('openapi')}")
    print(f"API Title: {spec.get('info', {}).get('title')}")
    print(f"API Version: {spec.get('info', {}).get('version')}")
    print(f"Total Servers: {len(spec.get('servers', []))}")
    print(f"Total Paths: {len(spec.get('paths', {}))}")
    print(f"Total Tags: {len(spec.get('tags', []))}")
    print(f"Total Schemas: {len(spec.get('components', {}).get('schemas', {}))}")
    print(f"Total Security Schemes: {len(spec.get('components', {}).get('securitySchemes', {}))}")
    
    # Validate specification
    validator = OpenAPIValidator(spec)
    validation_result = validator.validate()
    
    print(f"\n=== Validation Results ===")
    print(f"Valid: {validation_result['valid']}")
    
    if validation_result['errors']:
        print("Errors:")
        for error in validation_result['errors']:
            print(f"  - {error}")
    
    if validation_result['warnings']:
        print("Warnings:")
        for warning in validation_result['warnings']:
            print(f"  - {warning}")
```

## 📚 References

- [OpenAPI 3.0 Specification](https://swagger.io/specification/)
- [Swagger UI Documentation](https://swagger.io/tools/swagger-ui/)
- [API Design Best Practices](https://restfulapi.net/)

---

**Last Updated**: May 12, 2026  
**Version**: 1.0.0  
**Component**: OpenAPI/Swagger Documentation Service
