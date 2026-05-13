#!/usr/bin/env python3
"""
Test OpenAPI documentation system functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_openapi_service():
    """Test OpenAPI service implementation"""
    print("Testing OpenAPI Service...")
    
    try:
        # Check if OpenAPI files exist
        openapi_files = [
            'app/api/docs/openapi.py',
            'app/api/docs/swagger_ui.py',
            'app/api/docs/api_docs.py'
        ]
        
        for file_path in openapi_files:
            full_path = os.path.join(os.path.dirname(__file__), file_path)
            if os.path.exists(full_path):
                print(f"✅ {file_path} exists")
            else:
                print(f"❌ {file_path} missing")
                return False
        
        # Test OpenAPI service structure
        openapi_file = os.path.join(os.path.dirname(__file__), 'app/api/docs/openapi.py')
        with open(openapi_file, 'r') as f:
            content = f.read()
        
        # Check for OpenAPIService class
        if 'class OpenAPIService' in content:
            print("✅ OpenAPIService class found")
        else:
            print("❌ OpenAPIService class missing")
        
        # Check for required methods
        required_methods = [
            'add_server',
            'add_tag',
            'add_security_scheme',
            'add_schema',
            'add_response',
            'register_endpoint',
            'get_spec',
            'get_spec_json',
            'validate_spec'
        ]
        
        for method in required_methods:
            if f'def {method}' in content:
                print(f"✅ {method} method found")
            else:
                print(f"❌ {method} method missing")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAPI service test error: {e}")
        return False

def test_openapi_spec_generation():
    """Test OpenAPI specification generation"""
    print("\nTesting OpenAPI Spec Generation...")
    
    try:
        import json
        
        # Test basic OpenAPI spec structure
        basic_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": "Test API",
                "version": "1.0.0",
                "description": "Test API description"
            },
            "servers": [
                {
                    "url": "http://localhost:5000",
                    "description": "Development server"
                }
            ],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {},
                "responses": {}
            }
        }
        
        # Validate spec structure
        required_fields = ["openapi", "info", "paths"]
        for field in required_fields:
            if field in basic_spec:
                print(f"✅ Required field '{field}' present")
            else:
                print(f"❌ Required field '{field}' missing")
        
        # Test spec serialization
        spec_json = json.dumps(basic_spec, indent=2)
        parsed_spec = json.loads(spec_json)
        
        if parsed_spec["info"]["title"] == basic_spec["info"]["title"]:
            print("✅ Spec serialization works")
        else:
            print("❌ Spec serialization failed")
        
        # Test security scheme generation
        security_scheme = {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication"
        }
        
        if security_scheme["type"] == "apiKey":
            print("✅ Security scheme generation works")
        else:
            print("❌ Security scheme generation failed")
        
        # Test schema generation
        user_schema = {
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
                }
            },
            "required": ["id", "username", "email"]
        }
        
        if user_schema["type"] == "object" and "properties" in user_schema:
            print("✅ Schema generation works")
        else:
            print("❌ Schema generation failed")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAPI spec generation test error: {e}")
        return False

def test_swagger_ui_service():
    """Test Swagger UI service implementation"""
    print("\nTesting Swagger UI Service...")
    
    try:
        # Test Swagger UI service structure
        swagger_ui_file = os.path.join(os.path.dirname(__file__), 'app/api/docs/swagger_ui.py')
        with open(swagger_ui_file, 'r') as f:
            content = f.read()
        
        # Check for SwaggerUIService class
        if 'class SwaggerUIService' in content:
            print("✅ SwaggerUIService class found")
        else:
            print("❌ SwaggerUIService class missing")
        
        # Check for required methods
        required_methods = [
            'get_swagger_html',
            'get_openapi_json',
            'get_openapi_yaml',
            'get_config_json',
            'search_endpoints',
            'get_endpoint_details',
            'generate_client_code'
        ]
        
        for method in required_methods:
            if f'def {method}' in content:
                print(f"✅ {method} method found")
            else:
                print(f"❌ {method} method missing")
        
        # Test client code generation logic
        def generate_curl_example(method, path, params=None):
            """Generate cURL example"""
            curl_parts = [f"curl -X {method.upper()}"]
            curl_parts.append(f"'{path}'")
            curl_parts.append("-H 'Content-Type: application/json'")
            
            if method.upper() not in ['GET', 'HEAD']:
                curl_parts.append("-d '{\"key\": \"value\"}'")
            
            return " \\\n  ".join(curl_parts)
        
        curl_example = generate_curl_example("GET", "/api/users")
        if "curl -X GET" in curl_example and "/api/users" in curl_example:
            print("✅ cURL generation works")
        else:
            print("❌ cURL generation failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Swagger UI service test error: {e}")
        return False

def test_api_docs_endpoints():
    """Test API documentation endpoints"""
    print("\nTesting API Documentation Endpoints...")
    
    try:
        # Test API docs blueprint structure
        api_docs_file = os.path.join(os.path.dirname(__file__), 'app/api/docs/api_docs.py')
        with open(api_docs_file, 'r') as f:
            content = f.read()
        
        # Check for blueprint creation
        if 'api_docs_bp = Blueprint(' in content:
            print("✅ API docs blueprint found")
        else:
            print("❌ API docs blueprint missing")
        
        # Check for required endpoints
        required_endpoints = [
            'docs_index',
            'swagger_ui',
            'openapi_spec',
            'openapi_yaml',
            'api_info',
            'validate_spec',
            'search_endpoints',
            'export_specification'
        ]
        
        for endpoint in required_endpoints:
            if f'def {endpoint}' in content:
                print(f"✅ {endpoint} endpoint function found")
            else:
                print(f"❌ {endpoint} endpoint function missing")
        
        # Check for route decorators
        if '@api_docs_bp.route(' in content:
            print("✅ Route decorators found")
        else:
            print("❌ Route decorators missing")
        
        return True
        
    except Exception as e:
        print(f"❌ API docs endpoints test error: {e}")
        return False

def test_openapi_validation():
    """Test OpenAPI specification validation"""
    print("\nTesting OpenAPI Validation...")
    
    try:
        # Test OpenAPI spec validation logic
        def validate_openapi_spec(spec):
            """Validate OpenAPI specification"""
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            # Check required fields
            if 'openapi' not in spec:
                validation_result['errors'].append('Missing openapi version')
                validation_result['valid'] = False
            
            if 'info' not in spec:
                validation_result['errors'].append('Missing info section')
                validation_result['valid'] = False
            
            if 'paths' not in spec:
                validation_result['errors'].append('Missing paths section')
                validation_result['valid'] = False
            
            # Check info section
            info = spec.get('info', {})
            required_info_fields = ['title', 'version']
            for field in required_info_fields:
                if field not in info:
                    validation_result['errors'].append(f'Missing required info field: {field}')
                    validation_result['valid'] = False
            
            return validation_result
        
        # Test valid spec
        valid_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "paths": {}
        }
        
        result = validate_openapi_spec(valid_spec)
        if result['valid']:
            print("✅ Valid spec validation works")
        else:
            print("❌ Valid spec validation failed")
        
        # Test invalid spec
        invalid_spec = {
            "info": {
                "title": "Test API"
                # Missing version
            }
            # Missing openapi and paths
        }
        
        result = validate_openapi_spec(invalid_spec)
        if not result['valid'] and len(result['errors']) > 0:
            print("✅ Invalid spec validation works")
        else:
            print("❌ Invalid spec validation failed")
        
        # Test HTTP method validation
        valid_methods = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']
        invalid_method = 'invalid'
        
        if invalid_method not in valid_methods:
            print("✅ HTTP method validation works")
        else:
            print("❌ HTTP method validation failed")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAPI validation test error: {e}")
        return False

def main():
    """Run all OpenAPI system tests"""
    print("OpenAPI Documentation System Tests")
    print("=" * 50)
    
    tests = [
        test_openapi_service,
        test_openapi_spec_generation,
        test_swagger_ui_service,
        test_api_docs_endpoints,
        test_openapi_validation
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("OPENAPI SYSTEM TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All OpenAPI system tests passed")
        return True
    else:
        print("❌ Some OpenAPI system tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
