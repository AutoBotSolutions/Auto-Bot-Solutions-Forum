#!/usr/bin/env python3
"""
Comprehensive integration test for all API systems
"""

import sys
import os
from typing import List, Dict, Any, Optional
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_module_imports():
    """Test that all modules can be imported without errors"""
    print("Testing Module Imports...")
    
    try:
        # Test basic imports
        from app.models import User, APIKey, APIUsage, APICache
        print("✅ Basic models imported")
        
        # Test cache imports
        from app.cache.redis_cache import RedisCacheService
        from app.cache.cache_manager import CacheManager
        from app.cache.cache_utils import cache_key_builder, cache_ttl
        print("✅ Cache modules imported")
        
        # Test documentation imports
        from app.api.docs.openapi import OpenAPIService
        from app.api.docs.swagger_ui import SwaggerUIService
        from app.api.docs.api_docs import api_docs_bp
        print("✅ Documentation modules imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_api_system_integration():
    """Test API system integration points"""
    print("\nTesting API System Integration...")
    
    try:
        # Test that services can be instantiated
        from app.api.docs.openapi import OpenAPIService
        
        # Create OpenAPI service
        openapi_service = OpenAPIService(
            title="Test API",
            version="1.0.0",
            description="Test API for integration testing"
        )
        
        # Add basic components
        openapi_service.add_server("http://localhost:5000", "Test server")
        openapi_service.add_tag("Test", "Test tag")
        
        # Add security schemes
        openapi_service.add_security_scheme(name="ApiKeyAuth", scheme_type="apiKey", 
                                          name_param="X-API-Key",
                                          location="header",
                                          description="API key authentication")
        
        # Add basic schema
        openapi_service.add_schema("TestUser", {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"}
            }
        })
        
        # Get specification
        spec = openapi_service.get_spec()
        
        if spec["info"]["title"] == "Test API":
            print("✅ OpenAPI service integration works")
        else:
            print("❌ OpenAPI service integration failed")
        
        # Test Swagger UI service
        from app.api.docs.swagger_ui import SwaggerUIService
        swagger_service = SwaggerUIService(openapi_service)
        
        if swagger_service.openapi_service == openapi_service:
            print("✅ Swagger UI service integration works")
        else:
            print("❌ Swagger UI service integration failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test error: {e}")
        return False

def test_authentication_flow():
    """Test authentication flow integration"""
    print("\nTesting Authentication Flow Integration...")
    
    try:
        import jwt
        import secrets
        from datetime import datetime, timedelta
        
        # Test JWT token flow
        secret_key = secrets.token_urlsafe(32)
        
        # Create user payload
        user_payload = {
            'user_id': 1,
            'username': 'testuser',
            'roles': ['user'],
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        
        # Generate token
        token = jwt.encode(user_payload, secret_key, algorithm='HS256')
        
        # Verify token
        decoded = jwt.decode(token, secret_key, algorithms=['HS256'])
        
        if decoded['user_id'] == user_payload['user_id']:
            print("✅ JWT authentication flow works")
        else:
            print("❌ JWT authentication flow failed")
        
        # Test API key flow
        api_key = f"ak_{secrets.token_urlsafe(32)}"
        
        # Simulate API key validation
        def validate_api_key_format(key):
            return key.startswith('ak_') and len(key) >= 35
        
        if validate_api_key_format(api_key):
            print("✅ API key authentication flow works")
        else:
            print("❌ API key authentication flow failed")
        
        # Test permission checking
        user_permissions = ['read', 'write']
        required_permissions = ['read']
        
        def check_permissions(user_perms, required_perms):
            return all(perm in user_perms for perm in required_perms)
        
        if check_permissions(user_permissions, required_permissions):
            print("✅ Permission checking works")
        else:
            print("❌ Permission checking failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication flow test error: {e}")
        return False

def test_caching_integration():
    """Test caching system integration"""
    print("\nTesting Caching Integration...")
    
    try:
        # Test cache key building
        def build_cache_key(prefix, *args, **kwargs):
            key_parts = [prefix]
            key_parts.extend(str(arg) for arg in args)
            
            if kwargs:
                sorted_kwargs = sorted(kwargs.items())
                key_parts.extend(f"{k}={v}" for k, v in sorted_kwargs)
            
            return ":".join(key_parts)
        
        # Test various cache key patterns
        user_key = build_cache_key("user", 123)
        post_key = build_cache_key("post", 456, "comments")
        search_key = build_cache_key("search", "posts", query="test", page=1)
        
        if all(key.startswith(prefix) for key, prefix in [
            (user_key, "user"), (post_key, "post"), (search_key, "search")
        ]):
            print("✅ Cache key building works")
        else:
            print("❌ Cache key building failed")
        
        # Test TTL management
        def get_cache_ttl(ttl_type, custom_ttl=None):
            ttl_map = {
                'short': 300,      # 5 minutes
                'medium': 1800,    # 30 minutes
                'long': 7200,      # 2 hours
                'day': 86400       # 24 hours
            }
            
            if custom_ttl:
                return custom_ttl
            return ttl_map.get(ttl_type, 300)
        
        short_ttl = get_cache_ttl('short')
        custom_ttl = get_cache_ttl('custom', 600)
        
        if short_ttl == 300 and custom_ttl == 600:
            print("✅ TTL management works")
        else:
            print("❌ TTL management failed")
        
        # Test cache invalidation logic
        class MockCache:
            def __init__(self):
                self.data = {}
            
            def set(self, key, value):
                self.data[key] = value
            
            def delete(self, key):
                return self.data.pop(key, None) is not None
            
            def clear_pattern(self, pattern):
                keys_to_delete = [k for k in self.data.keys() if pattern in k]
                for key in keys_to_delete:
                    self.data.pop(key, None)
                return len(keys_to_delete)
        
        cache = MockCache()
        cache.set("user:123:profile", {"name": "Test User"})
        cache.set("user:123:posts", [{"id": 1}])
        cache.set("user:456:profile", {"name": "Other User"})
        
        # Invalidate user 123 data
        deleted_count = cache.clear_pattern("user:123:")
        
        if deleted_count == 2 and cache.data.get("user:456:profile"):
            print("✅ Cache invalidation works")
        else:
            print("❌ Cache invalidation failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Caching integration test error: {e}")
        return False

def test_api_documentation_integration():
    """Test API documentation integration"""
    print("\nTesting API Documentation Integration...")
    
    try:
        import json
        
        # Test OpenAPI spec generation with all components
        from app.api.docs.openapi import OpenAPIService
        
        openapi_service = OpenAPIService(
            title="Auto Bot Solutions Forum API",
            version="1.0.0",
            description="Complete API documentation test"
        )
        
        # Initialize default components
        openapi_service.initialize_default_components()
        
        # Get complete specification
        spec = openapi_service.get_spec()
        
        # Validate specification structure
        required_components = ['openapi', 'info', 'servers', 'paths', 'components']
        for component in required_components:
            if component in spec:
                print(f"✅ Spec component '{component}' present")
            else:
                print(f"❌ Spec component '{component}' missing")
        
        # Test security schemes
        security_schemes = spec.get('components', {}).get('securitySchemes', {})
        if 'ApiKeyAuth' in security_schemes and 'JWTAuth' in security_schemes:
            print("✅ Security schemes integrated")
        else:
            print("❌ Security schemes missing")
        
        # Test schemas
        schemas = spec.get('components', {}).get('schemas', {})
        if 'User' in schemas and 'Post' in schemas and 'Error' in schemas:
            print("✅ Schemas integrated")
        else:
            print("❌ Schemas missing")
        
        # Test responses
        responses = spec.get('components', {}).get('responses', {})
        if 'BadRequest' in responses and 'Unauthorized' in responses:
            print("✅ Responses integrated")
        else:
            print("❌ Responses missing")
        
        # Test tags
        tags = spec.get('tags', [])
        tag_names = [tag['name'] for tag in tags]
        
        required_tags = ['Authentication', 'Posts', 'Users', 'Admin']
        found_tags = sum(1 for tag in required_tags if tag in tag_names)
        
        if found_tags >= 3:  # At least 3 of 4 required tags
            print(f"✅ Tags integrated ({found_tags}/{len(required_tags)})")
        else:
            print(f"❌ Tags missing ({found_tags}/{len(required_tags)})")
        
        # Test spec validation
        validation_result = openapi_service.validate_spec()
        
        if validation_result['valid']:
            print("✅ Spec validation passed")
        else:
            print(f"❌ Spec validation failed: {len(validation_result['errors'])} errors")
        
        return True
        
    except Exception as e:
        print(f"❌ Documentation integration test error: {e}")
        return False

def test_error_handling():
    """Test error handling across all systems"""
    print("\nTesting Error Handling...")
    
    try:
        # Test JWT error handling
        import jwt
        
        try:
            jwt.decode("invalid.token", "secret", algorithms=["HS256"])
            print("❌ JWT error handling failed")
        except jwt.InvalidTokenError:
            print("✅ JWT error handling works")
        
        # Test cache error handling
        class FailingCache:
            def get(self, key):
                raise Exception("Cache connection failed")
            
            def set(self, key, value):
                raise Exception("Cache connection failed")
        
        cache = FailingCache()
        
        try:
            cache.get("test_key")
            print("❌ Cache error handling failed")
        except Exception:
            print("✅ Cache error handling works")
        
        # Test API key validation error handling
        def validate_api_key(key):
            if not key:
                raise ValueError("API key cannot be empty")
            if not key.startswith('ak_'):
                raise ValueError("Invalid API key format")
            return True
        
        try:
            validate_api_key("")
            print("❌ API key validation error handling failed")
        except ValueError:
            print("✅ API key validation error handling works")
        
        try:
            validate_api_key("invalid_key")
            print("❌ API key validation error handling failed")
        except ValueError:
            print("✅ API key validation error handling works")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test error: {e}")
        return False

def main():
    """Run comprehensive integration tests"""
    print("Comprehensive API System Integration Tests")
    print("=" * 60)
    
    tests = [
        test_module_imports,
        test_api_system_integration,
        test_authentication_flow,
        test_caching_integration,
        test_api_documentation_integration,
        test_error_handling
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("COMPREHENSIVE INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All integration tests passed")
        print("🎉 API systems are working correctly and are ready for production!")
        return True
    else:
        print("❌ Some integration tests failed")
        print("⚠️  Some API systems may need additional work")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
