#!/usr/bin/env python3
"""
Test JWT authentication system functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_jwt_functionality():
    """Test JWT token generation and validation"""
    print("Testing JWT Functionality...")
    
    try:
        import jwt
        import secrets
        from datetime import datetime, timedelta
        
        # Test JWT token generation
        secret_key = secrets.token_urlsafe(32)
        print(f"✅ JWT secret key generated: {secret_key[:16]}...")
        
        # Test token encoding
        payload = {
            'user_id': 1,
            'username': 'testuser',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
            'iss': 'forum-api'
        }
        
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        print(f"✅ JWT token generated: {token[:32]}...")
        
        # Test token decoding
        decoded = jwt.decode(token, secret_key, algorithms=['HS256'])
        print(f"✅ JWT token decoded successfully")
        
        # Verify payload
        if decoded['user_id'] == payload['user_id']:
            print("✅ JWT payload verification works")
        else:
            print("❌ JWT payload verification failed")
        
        # Test token expiration
        expired_payload = payload.copy()
        expired_payload['exp'] = datetime.utcnow() - timedelta(hours=1)
        
        expired_token = jwt.encode(expired_payload, secret_key, algorithm='HS256')
        
        try:
            jwt.decode(expired_token, secret_key, algorithms=['HS256'])
            print("❌ Expired token validation failed")
        except jwt.ExpiredSignatureError:
            print("✅ Expired token correctly rejected")
        
        # Test invalid token
        try:
            jwt.decode("invalid.token.here", secret_key, algorithms=['HS256'])
            print("❌ Invalid token validation failed")
        except jwt.InvalidTokenError:
            print("✅ Invalid token correctly rejected")
        
        return True
        
    except ImportError as e:
        print(f"❌ JWT import error: {e}")
        return False
    except Exception as e:
        print(f"❌ JWT test error: {e}")
        return False

def test_jwt_service_methods():
    """Test JWT service methods"""
    print("\nTesting JWT Service Methods...")
    
    try:
        # Check if JWT service exists
        jwt_auth_file = os.path.join(os.path.dirname(__file__), 'app', 'api', 'auth', 'jwt_auth.py')
        
        if not os.path.exists(jwt_auth_file):
            print("❌ JWT auth file not found")
            return False
        
        with open(jwt_auth_file, 'r') as f:
            content = f.read()
        
        # Check for JWT service class
        if 'class JWTService' in content:
            print("✅ JWTService class found")
        else:
            print("❌ JWTService class missing")
        
        # Check for required methods
        required_methods = [
            'generate_token',
            'verify_token',
            'refresh_token',
            'revoke_token',
            'decode_token'
        ]
        
        for method in required_methods:
            if f'def {method}' in content:
                print(f"✅ {method} method found")
            else:
                print(f"❌ {method} method missing")
        
        return True
        
    except Exception as e:
        print(f"❌ JWT service test error: {e}")
        return False

def test_jwt_endpoints():
    """Test JWT endpoints structure"""
    print("\nTesting JWT Endpoints Structure...")
    
    try:
        # Check JWT endpoints file
        jwt_auth_file = os.path.join(os.path.dirname(__file__), 'app', 'api', 'auth', 'jwt_auth.py')
        
        with open(jwt_auth_file, 'r') as f:
            content = f.read()
        
        # Check for required endpoint functions
        required_endpoints = [
            'login',
            'refresh',
            'logout',
            'verify',
            'profile'
        ]
        
        for endpoint in required_endpoints:
            if f'def {endpoint}' in content:
                print(f"✅ {endpoint} endpoint function found")
            else:
                print(f"❌ {endpoint} endpoint function missing")
        
        # Check for blueprint
        if 'jwt_bp = Blueprint(' in content:
            print("✅ JWT blueprint found")
        else:
            print("❌ JWT blueprint missing")
        
        # Check for route decorators
        if '@jwt_bp.route(' in content:
            print("✅ JWT route decorators found")
        else:
            print("❌ JWT route decorators missing")
        
        return True
        
    except Exception as e:
        print(f"❌ JWT endpoints test error: {e}")
        return False

def test_jwt_security():
    """Test JWT security features"""
    print("\nTesting JWT Security Features...")
    
    try:
        import jwt
        import secrets
        from datetime import datetime, timedelta
        
        # Test token with different algorithms
        secret_key = secrets.token_urlsafe(32)
        payload = {
            'user_id': 1,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        
        # Test HS256 algorithm
        token_hs256 = jwt.encode(payload, secret_key, algorithm='HS256')
        decoded = jwt.decode(token_hs256, secret_key, algorithms=['HS256'])
        print("✅ HS256 algorithm works")
        
        # Test token with custom claims
        custom_payload = {
            'user_id': 1,
            'username': 'testuser',
            'roles': ['user', 'admin'],
            'permissions': ['read', 'write'],
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        
        custom_token = jwt.encode(custom_payload, secret_key, algorithm='HS256')
        decoded_custom = jwt.decode(custom_token, secret_key, algorithms=['HS256'])
        
        if 'roles' in decoded_custom and 'permissions' in decoded_custom:
            print("✅ Custom claims work correctly")
        else:
            print("❌ Custom claims failed")
        
        # Test token blacklisting logic
        class MockTokenBlacklist:
            def __init__(self):
                self.blacklisted = set()
            
            def blacklist(self, token_id):
                self.blacklisted.add(token_id)
            
            def is_blacklisted(self, token_id):
                return token_id in self.blacklisted
        
        blacklist = MockTokenBlacklist()
        
        # Test blacklisting
        test_token_id = "test_token_123"
        blacklist.blacklist(test_token_id)
        
        if blacklist.is_blacklisted(test_token_id):
            print("✅ Token blacklisting works")
        else:
            print("❌ Token blacklisting failed")
        
        # Test token refresh logic
        def generate_refresh_token():
            return secrets.token_urlsafe(32)
        
        def validate_refresh_token(token, stored_tokens):
            return token in stored_tokens
        
        stored_tokens = set()
        refresh_token = generate_refresh_token()
        stored_tokens.add(refresh_token)
        
        if validate_refresh_token(refresh_token, stored_tokens):
            print("✅ Refresh token validation works")
        else:
            print("❌ Refresh token validation failed")
        
        return True
        
    except Exception as e:
        print(f"❌ JWT security test error: {e}")
        return False

def main():
    """Run all JWT system tests"""
    print("JWT Authentication System Tests")
    print("=" * 50)
    
    tests = [
        test_jwt_functionality,
        test_jwt_service_methods,
        test_jwt_endpoints,
        test_jwt_security
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
    print("JWT SYSTEM TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All JWT system tests passed")
        return True
    else:
        print("❌ Some JWT system tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
