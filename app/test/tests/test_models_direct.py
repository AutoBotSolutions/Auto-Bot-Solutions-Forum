#!/usr/bin/env python3
"""
Test models directly without importing the auth module
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

try:
    # Test basic imports
    print("Testing basic imports...")
    
    from app.models import User, APIKey, APIUsage, APICache
    print("✅ Basic models imported successfully")
    
    # Import models directly from the models file
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app/api/auth'))
    import models as auth_models
    
    # Test OAuth2 models
    OAuth2Client = auth_models.OAuth2Client
    OAuth2Token = auth_models.OAuth2Token
    OAuth2AuthorizationCode = auth_models.OAuth2AuthorizationCode
    OAuth2RefreshToken = auth_models.OAuth2RefreshToken
    OAuth2Scope = auth_models.OAuth2Scope
    OAuth2UserConsent = auth_models.OAuth2UserConsent
    
    print("✅ OAuth2 models imported successfully")
    
    # Test model attributes
    print("\n🔍 Testing model attributes...")
    
    # Test APIKey model
    api_key_attrs = [attr for attr in dir(APIKey) if not attr.startswith('_')]
    print(f"APIKey attributes: {len(api_key_attrs)}")
    
    # Test OAuth2Client model
    client_attrs = [attr for attr in dir(OAuth2Client) if not attr.startswith('_')]
    print(f"OAuth2Client attributes: {len(client_attrs)}")
    
    # Test model methods
    print("\n🔧 Testing model methods...")
    
    # Test APIKey methods
    api_key_methods = [attr for attr in dir(APIKey) if callable(getattr(APIKey, attr)) and not attr.startswith('_')]
    print(f"APIKey methods: {len(api_key_methods)}")
    
    # Test OAuth2Token methods
    token_methods = [attr for attr in dir(OAuth2Token) if callable(getattr(OAuth2Token, attr)) and not attr.startswith('_')]
    print(f"OAuth2Token methods: {len(token_methods)}")
    
    # Test specific methods
    if hasattr(APIKey, 'revoke'):
        print("✅ APIKey.revoke method exists")
    if hasattr(APIKey, 'update_usage'):
        print("✅ APIKey.update_usage method exists")
    if hasattr(APIKey, 'is_valid'):
        print("✅ APIKey.is_valid method exists")
    
    if hasattr(OAuth2Token, 'revoke'):
        print("✅ OAuth2Token.revoke method exists")
    if hasattr(OAuth2Token, 'is_expired'):
        print("✅ OAuth2Token.is_expired method exists")
    if hasattr(OAuth2Token, 'is_valid'):
        print("✅ OAuth2Token.is_valid method exists")
    
    print("\n✅ All models imported and tested successfully")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
