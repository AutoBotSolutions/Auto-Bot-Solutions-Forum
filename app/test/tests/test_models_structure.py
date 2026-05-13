#!/usr/bin/env python3
"""
Test model structure without database access
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

try:
    # Test basic imports
    print("Testing model structure...")
    
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
    
    # Test model structure without database access
    print("\n🔍 Testing model structure...")
    
    # Test APIKey model structure
    api_key_attrs = [attr for attr in dir(APIKey) if not attr.startswith('_')]
    api_key_fields = [attr for attr in api_key_attrs if not callable(getattr(APIKey, attr, None))]
    print(f"APIKey fields: {len(api_key_fields)}")
    print(f"APIKey fields: {[f for f in api_key_fields if f in ['id', 'name', 'key_hash', 'api_key', 'user_id', 'permissions', 'created_at', 'expires_at', 'is_active']]}")
    
    # Test OAuth2Client model structure
    client_attrs = [attr for attr in dir(OAuth2Client) if not attr.startswith('_')]
    client_fields = [attr for attr in client_attrs if not callable(getattr(OAuth2Client, attr, None))]
    print(f"OAuth2Client fields: {len(client_fields)}")
    
    # Test OAuth2Token model structure
    token_attrs = [attr for attr in dir(OAuth2Token) if not attr.startswith('_')]
    token_fields = [attr for attr in token_attrs if not callable(getattr(OAuth2Token, attr, None))]
    print(f"OAuth2Token fields: {len(token_fields)}")
    
    # Test model inheritance
    print("\n🧬 Testing model inheritance...")
    
    # Check if models inherit from SQLAlchemy Model
    print(f"APIKey inherits from db.Model: {'db.Model' in str(APIKey.__mro__)}")
    print(f"OAuth2Client inherits from db.Model: {'db.Model' in str(OAuth2Client.__mro__)}")
    
    # Check if OAuth2 models have mixins
    client_mro = str(OAuth2Client.__mro__)
    print(f"OAuth2Client has OAuth2ClientMixin: {'OAuth2ClientMixin' in client_mro}")
    
    token_mro = str(OAuth2Token.__mro__)
    print(f"OAuth2Token has OAuth2TokenMixin: {'OAuth2TokenMixin' in token_mro}")
    
    # Test model table names
    print("\n📋 Testing model table names...")
    
    print(f"APIKey table: {getattr(APIKey, '__tablename__', 'N/A')}")
    print(f"OAuth2Client table: {getattr(OAuth2Client, '__tablename__', 'N/A')}")
    print(f"OAuth2Token table: {getattr(OAuth2Token, '__tablename__', 'N/A')}")
    print(f"OAuth2AuthorizationCode table: {getattr(OAuth2AuthorizationCode, '__tablename__', 'N/A')}")
    print(f"OAuth2RefreshToken table: {getattr(OAuth2RefreshToken, '__tablename__', 'N/A')}")
    
    # Test model relationships
    print("\n🔗 Testing model relationships...")
    
    # Check for relationship attributes
    api_key_relationships = [attr for attr in api_key_attrs if hasattr(APIKey, attr) and 'relationship' in str(type(getattr(APIKey, attr)))]
    print(f"APIKey relationships: {len(api_key_relationships)}")
    
    # Test model methods (non-database)
    print("\n🔧 Testing model methods (static/class methods)...")
    
    # Check for static methods
    api_key_static_methods = [attr for attr in dir(APIKey) if hasattr(APIKey, attr) and isinstance(getattr(APIKey, attr), staticmethod)]
    print(f"APIKey static methods: {len(api_key_static_methods)}")
    
    oauth2_static_methods = [attr for attr in dir(OAuth2Token) if hasattr(OAuth2Token, attr) and isinstance(getattr(OAuth2Token, attr), staticmethod)]
    print(f"OAuth2Token static methods: {len(oauth2_static_methods)}")
    
    print("\n✅ Model structure test completed successfully")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
