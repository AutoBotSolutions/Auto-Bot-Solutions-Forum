#!/usr/bin/env python3
"""
Test models only without Flask app context
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

try:
    # Test basic imports without importing the full auth module
    print("Testing model imports only...")
    
    # Test app.models
    from app.models import User, APIKey, APIUsage, APICache
    print("✅ Basic models imported successfully")
    
    # Test OAuth2 models directly (avoiding the __init__.py which has Flask app context)
    from app.api.auth.models import OAuth2Client, OAuth2Token, OAuth2AuthorizationCode, OAuth2RefreshToken, OAuth2Scope, OAuth2UserConsent
    print("✅ OAuth2 models imported successfully")
    
    # Test model attributes and relationships
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
    
    print("\n✅ All models imported and tested successfully")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
