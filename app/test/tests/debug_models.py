#!/usr/bin/env python3
"""
Debug script to verify database models are properly integrated
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

try:
    from app.models import User, APIKey, APIUsage, APICache
    from app.api.auth.models import OAuth2Client, OAuth2Token, OAuth2AuthorizationCode, OAuth2RefreshToken, OAuth2Scope, OAuth2UserConsent
    print("✅ All models imported successfully")
    
    # Test model relationships
    print("\n🔍 Testing model relationships...")
    
    # Test APIKey model
    try:
        print(f"APIKey model attributes: {[attr for attr in dir(APIKey) if not attr.startswith('_')]}")
        print(f"APIKey user relationship: {hasattr(APIKey, 'user')}")
        print(f"APIKey usage relationship: {hasattr(APIKey, 'usage_logs')}")
    except Exception as e:
        print(f"❌ APIKey model error: {e}")
    
    # Test OAuth2 models
    try:
        print(f"OAuth2Client model attributes: {[attr for attr in dir(OAuth2Client) if not attr.startswith('_')]}")
        print(f"OAuth2Client user relationship: {hasattr(OAuth2Client, 'user')}")
        print(f"OAuth2Client tokens relationship: {hasattr(OAuth2Client, 'tokens')}")
    except Exception as e:
        print(f"❌ OAuth2Client model error: {e}")
    
    # Test model methods
    print("\n🔧 Testing model methods...")
    
    # Test APIKey methods
    try:
        if hasattr(APIKey, 'revoke'):
            print("✅ APIKey.revoke method exists")
        if hasattr(APIKey, 'update_usage'):
            print("✅ APIKey.update_usage method exists")
        if hasattr(APIKey, 'is_valid'):
            print("✅ APIKey.is_valid method exists")
    except Exception as e:
        print(f"❌ APIKey methods error: {e}")
    
    # Test OAuth2Token methods
    try:
        if hasattr(OAuth2Token, 'revoke'):
            print("✅ OAuth2Token.revoke method exists")
        if hasattr(OAuth2Token, 'is_expired'):
            print("✅ OAuth2Token.is_expired method exists")
        if hasattr(OAuth2Token, 'is_valid'):
            print("✅ OAuth2Token.is_valid method exists")
    except Exception as e:
        print(f"❌ OAuth2Token methods error: {e}")
    
    print("\n✅ Database models integration test completed")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
