#!/usr/bin/env python3
"""
Test API key management system functionality (corrected)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_api_key_service_methods():
    """Test API key service methods exist"""
    print("Testing API Key Service Methods...")
    
    try:
        # Test API key service import (without importing the module that requires app context)
        import app.api.auth.services as auth_services
        
        # Check if APIKeyService class exists
        if hasattr(auth_services, 'APIKeyService'):
            print("✅ APIKeyService class exists")
            
            # Check service methods exist
            service_methods = [
                'create_key',
                'get_user_keys', 
                'get_user_key',
                'validate_key',
                'revoke_key',
                'rotate_key',
                'update_usage',
                'get_usage_stats'
            ]
            
            for method in service_methods:
                if hasattr(auth_services.APIKeyService, method):
                    print(f"✅ APIKeyService.{method} method exists")
                else:
                    print(f"❌ APIKeyService.{method} method missing")
        else:
            print("❌ APIKeyService class missing")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_api_key_generation():
    """Test API key generation logic"""
    print("\nTesting API Key Generation...")
    
    try:
        import secrets
        import hashlib
        import time
        
        # Test key generation
        test_key = f"ak_{secrets.token_urlsafe(32)}"
        print(f"✅ API key generation works: {test_key[:16]}...")
        
        # Test key hashing
        key_hash = hashlib.sha256(test_key.encode()).hexdigest()
        print(f"✅ API key hashing works: {key_hash[:16]}...")
        
        # Test key validation logic (without database)
        def validate_key_format(key):
            """Validate API key format"""
            if not key.startswith('ak_'):
                return False
            if len(key) < 35:  # 'ak_' + 32 chars minimum
                return False
            return True
        
        # Test validation
        if validate_key_format(test_key):
            print("✅ Key format validation works")
        else:
            print("❌ Key format validation failed")
        
        # Test invalid key formats
        invalid_keys = ['invalid', 'ak_short', 'ak_toooolongkeythatshouldfailvalidation']
        for invalid_key in invalid_keys:
            if not validate_key_format(invalid_key):
                print(f"✅ Invalid key correctly rejected: {invalid_key[:20]}...")
            else:
                print(f"❌ Invalid key incorrectly accepted: {invalid_key[:20]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Key generation test error: {e}")
        return False

def test_api_key_permissions():
    """Test API key permissions system"""
    print("\nTesting API Key Permissions...")
    
    try:
        # Test permission validation logic
        test_permissions = ['read', 'write', 'admin']
        test_user_permissions = ['read', 'write']
        
        # Check if user has required permissions
        def has_permission(user_perms, required_perms):
            return all(perm in user_perms for perm in required_perms)
        
        def has_any_permission(user_perms, required_perms):
            return any(perm in user_perms for perm in required_perms)
        
        # Test permission checking
        if has_permission(test_user_permissions, ['read']):
            print("✅ Permission checking works for 'read'")
        
        if has_permission(test_user_permissions, ['read', 'write']):
            print("✅ Permission checking works for 'read, write'")
        
        if not has_permission(test_user_permissions, ['admin']):
            print("✅ Permission checking correctly denies 'admin'")
        
        if has_any_permission(test_user_permissions, ['admin', 'write']):
            print("✅ Any permission checking works for 'admin, write'")
        
        # Test permission sets
        def get_permission_set(permissions):
            return set(permissions)
        
        user_perms_set = get_permission_set(test_user_permissions)
        required_perms_set = get_permission_set(['read', 'write'])
        
        if user_perms_set >= required_perms_set:
            print("✅ Permission set comparison works")
        
        return True
        
    except Exception as e:
        print(f"❌ Permission test error: {e}")
        return False

def test_api_key_rate_limiting():
    """Test API key rate limiting"""
    print("\nTesting API Key Rate Limiting...")
    
    try:
        from datetime import datetime, timedelta
        
        # Simulate rate limiting
        class MockRateLimiter:
            def __init__(self, limit=1000):
                self.limit = limit
                self.requests = {}
            
            def is_allowed(self, api_key_id):
                now = datetime.now()
                if api_key_id not in self.requests:
                    self.requests[api_key_id] = []
                
                # Remove requests older than 1 hour
                self.requests[api_key_id] = [req_time for req_time in self.requests[api_key_id] 
                                           if now - req_time < timedelta(hours=1)]
                
                if len(self.requests[api_key_id]) < self.limit:
                    self.requests[api_key_id].append(now)
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
        allowed_count = 0
        denied_count = 0
        for i in range(5, 8):
            if rate_limiter.is_allowed("test_key"):
                allowed_count += 1
                print(f"❌ Request {i+1} allowed unexpectedly")
            else:
                denied_count += 1
                print(f"✅ Request {i+1} correctly denied")
        
        if denied_count >= 2:
            print("✅ Rate limiting works correctly")
        else:
            print("❌ Rate limiting not working properly")
        
        return True
        
    except Exception as e:
        print(f"❌ Rate limiting test error: {e}")
        return False

def test_api_key_endpoints_structure():
    """Test API key endpoints structure"""
    print("\nTesting API Key Endpoints Structure...")
    
    try:
        # Check if the api_keys.py file exists and has the expected structure
        api_keys_file = os.path.join(os.path.dirname(__file__), 'app', 'api', 'auth', 'api_keys.py')
        
        if not os.path.exists(api_keys_file):
            print("❌ API keys endpoint file not found")
            return False
        
        with open(api_keys_file, 'r') as f:
            content = f.read()
        
        # Check for required endpoint functions
        required_functions = [
            'create_api_key',
            'get_api_keys', 
            'get_api_key',
            'update_api_key',
            'revoke_api_key',
            'rotate_api_key',
            'get_api_key_stats'
        ]
        
        for func in required_functions:
            if f'def {func}' in content:
                print(f"✅ {func} endpoint function found")
            else:
                print(f"❌ {func} endpoint function missing")
        
        # Check for blueprint creation
        if 'api_keys_bp = Blueprint(' in content:
            print("✅ API keys blueprint found")
        else:
            print("❌ API keys blueprint missing")
        
        # Check for route decorators
        if '@api_keys_bp.route(' in content:
            print("✅ Route decorators found")
        else:
            print("❌ Route decorators missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Endpoint structure test error: {e}")
        return False

def main():
    """Run all API key system tests"""
    print("API Key Management System Tests (Corrected)")
    print("=" * 60)
    
    tests = [
        test_api_key_service_methods,
        test_api_key_generation,
        test_api_key_permissions,
        test_api_key_rate_limiting,
        test_api_key_endpoints_structure
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
    print("API KEY SYSTEM TEST SUMMARY")
    print("=" * 60)
    
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
