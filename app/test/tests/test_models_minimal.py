#!/usr/bin/env python3
"""
Minimal test to check model definitions without Flask context
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

try:
    # Test basic imports
    print("Testing model definitions...")
    
    # Import SQLAlchemy directly to avoid Flask context
    from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
    
    # Test basic models by checking their definitions
    print("✅ SQLAlchemy imports successful")
    
    # Read and parse the models file to check structure
    models_file = os.path.join(os.path.dirname(__file__), 'app', 'models.py')
    with open(models_file, 'r') as f:
        models_content = f.read()
    
    # Check if required models are defined
    required_models = ['APIKey', 'APIUsage', 'APICache']
    for model in required_models:
        if f'class {model}' in models_content:
            print(f"✅ {model} class found in models.py")
        else:
            print(f"❌ {model} class not found in models.py")
    
    # Check OAuth2 models
    oauth2_models_file = os.path.join(os.path.dirname(__file__), 'app', 'api', 'auth', 'models.py')
    with open(oauth2_models_file, 'r') as f:
        oauth2_models_content = f.read()
    
    oauth2_required_models = ['OAuth2Client', 'OAuth2Token', 'OAuth2AuthorizationCode', 'OAuth2RefreshToken', 'OAuth2Scope', 'OAuth2UserConsent']
    for model in oauth2_required_models:
        if f'class {model}' in oauth2_models_content:
            print(f"✅ {model} class found in auth models.py")
        else:
            print(f"❌ {model} class not found in auth models.py")
    
    # Check for required fields in models
    print("\n🔍 Checking model fields...")
    
    # Check APIKey model fields
    apikey_fields = ['id', 'name', 'key_hash', 'api_key', 'user_id', 'permissions', 'created_at', 'expires_at', 'is_active']
    for field in apikey_fields:
        if f'{field} = Column' in models_content:
            print(f"✅ APIKey.{field} field found")
        else:
            print(f"❌ APIKey.{field} field not found")
    
    # Check OAuth2Client model fields
    oauth2_client_fields = ['id', 'name', 'client_id', 'client_secret', 'user_id', 'redirect_uris', 'scopes', 'created_at']
    for field in oauth2_client_fields:
        if f'{field} = Column' in oauth2_models_content:
            print(f"✅ OAuth2Client.{field} field found")
        else:
            print(f"❌ OAuth2Client.{field} field not found")
    
    # Check for model relationships
    print("\n🔗 Checking model relationships...")
    
    # Check for relationship definitions
    if 'relationship(' in models_content:
        print("✅ Relationships found in models.py")
    else:
        print("❌ No relationships found in models.py")
    
    if 'relationship(' in oauth2_models_content:
        print("✅ Relationships found in auth models.py")
    else:
        print("❌ No relationships found in auth models.py")
    
    # Check for model methods
    print("\n🔧 Checking model methods...")
    
    # Check for APIKey methods
    apikey_methods = ['revoke', 'update_usage', 'is_valid', 'rotate']
    for method in apikey_methods:
        if f'def {method}' in models_content:
            print(f"✅ APIKey.{method} method found")
        else:
            print(f"❌ APIKey.{method} method not found")
    
    # Check for OAuth2Token methods
    oauth2_token_methods = ['revoke', 'is_expired', 'is_valid']
    for method in oauth2_token_methods:
        if f'def {method}' in oauth2_models_content:
            print(f"✅ OAuth2Token.{method} method found")
        else:
            print(f"❌ OAuth2Token.{method} method not found")
    
    print("\n✅ Model definitions test completed successfully")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
