#!/usr/bin/env python3
"""
Simple test to check if models can be imported
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

try:
    # Test basic imports
    print("Testing basic imports...")
    
    # Test app.models
    from app.models import User, APIKey, APIUsage, APICache
    print("✅ Basic models imported successfully")
    
    # Test OAuth2 models
    from app.api.auth.models import OAuth2Client, OAuth2Token, OAuth2AuthorizationCode, OAuth2RefreshToken, OAuth2Scope, OAuth2UserConsent
    print("✅ OAuth2 models imported successfully")
    
    print("\n✅ All models imported successfully")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
