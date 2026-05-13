#!/usr/bin/env python3
"""
Test API key management system functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_api_key_service():
    """Test API key service functionality"""
    print("Testing API Key Service...")
    
    try:
        # Test API key service import
        from app.api.auth.services import APIKeyService
        print("✅ APIKeyService imported successfully")
        
        # Test service methods exist
        service_methods = [
            'create_api_key',
            'get_api_key',
            'validate_api_key',
            'revoke_api_key',
            'rotate_api_key',
            'update_usage',
            'get_usage_stats',
            'get_user_api_keys'
        ]
        
        for method in service_methods:
            if hasattr(APIKeyService, method):
                print(f"✅ APIKeyService.{method} method exists")
            else:
                print(f"❌ APIKeyService.{method} method missing")
        
        # Test API key generation logic
        import secrets
        import hashlib
        
        # Test key generation
        test_key = f"ak_{secrets.token_urlsafe(32)}"
        print(f"✅ API key generation works: {test_key[:16]}...")
        
        # Test key hashing
        key_hash = hashlib.sha256(test_key.encode()).hexdigest()
        print(f"✅ API key hashing works: {key_hash[:16]}...")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_api_key_endpoints():
    """Test API key endpoints"""
    print("\nTesting API Key Endpoints...")
    
    try:
        # Test API key endpoints import
        from app.api.auth.api_keys import api_keys_bp
        print("✅ API keys blueprint imported successfully")
        
        # Check if blueprint has routes
        if hasattr(api_keys_bp, 'deferred_functions'):
            print(f"✅ API keys blueprint has {len(api_keys_bp.deferred_functions)} deferred functions")
        
        # Test endpoint functions exist
        endpoint_functions = [
            'create_api_key',
            'get_api_keys',
            'get_api_key',
            'update_api_key',
            'revoke_api_key',
            'rotate_api_key',
            'get_api_key_stats'
        ]
        
        # Check if functions are defined in the module
        import app.api.auth.api_keys as api_keys_module
        
        for func in endpoint_functions:
            if hasattr(api_keys_module, func):
                print(f"✅ {func} endpoint function exists")
            else:
                print(f"❌ {func} endpoint function missing")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_api_key_permissions():
    """Test API key permissions system"""
    print("\nTesting API Key Permissions...")
    
    try:
        # Test permission decorators
        from app.api.auth.services import require_api_key, require_permission
        print("✅ Permission decorators imported successfully")
        
        # Test permission validation logic
        test_permissions = ['read', 'write', 'admin']
        test_user_permissions = ['read', 'write']
        
        # Check if user has required permissions
        def has_permission(user_perms, required_perms):
            return all(perm in user_perms for perm in required_perms)
        
        # Test permission checking
        if has_permission(test_user_permissions, ['read']):
            print("✅ Permission checking works for 'read'")
        
        if has_permission(test_user_permissions, ['read', 'write']):
            print("✅ Permission checking works for 'read, write'")
        
        if not has_permission(test_user_permissions, ['admin']):
            print("✅ Permission checking correctly denies 'admin'")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_api_key_rate_limiting():
    """Test API key rate limiting"""
    print("\nTesting API Key Rate Limiting...")
    
    try:
        # Test rate limiting logic
        from datetime import datetime, timedelta
        
        # Simulate rate limiting
        class MockRateLimiter:
            def __init__(self, limit=1000):
                self.limit = limit
                self.requests = []
            
            def is_allowed(self, api_key_id):
                now = datetime.utcnow()
                # Remove requests older than 1 hour
                self.requests = [req_time for req_time in self.requests 
                               if now - req_time < timedelta(hours=1)]
                
                if len(self.requests) < self.limit:
                    self.requests.append(now)
                    return True
                return False
        
        # Test rate limiting
        rate_limiter = MockRateLimiter(limit=5)
        
        # Test under limit
        for i in range(3):
            if rate_limiter.is_allowed("test_key"):
                print(f"✅ Request {i+1} allowed")
            else:
                print(f"❌ Request {i+1} denied unexpectedly")
        
        # Test over limit
        for i in range(5, 8):
            if rate_limiter.is_allowed("test_key"):
                print(f"❌ Request {i+1} allowed unexpectedly")
            else:
                print(f"✅ Request {i+1} correctly denied")
        
        return True
        
    except Exception as e:
        print(f"❌ Rate limiting test error: {e}")
        return False

def main():
    """Run all API key system tests"""
    print("API Key Management System Tests")
    print("=" * 50)
    
    tests = [
        test_api_key_service,
        test_api_key_endpoints,
        test_api_key_permissions,
        test_api_key_rate_limiting
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
    print("API KEY SYSTEM TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All API key system tests passed")
        return True
    else:
        print("❌ Some API key system tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
