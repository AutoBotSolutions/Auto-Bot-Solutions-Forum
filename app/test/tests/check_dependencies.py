#!/usr/bin/env python3
"""
Check for missing dependencies required by the API systems
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def check_dependency(name, import_name=None):
    """Check if a dependency is available"""
    if import_name is None:
        import_name = name
    
    try:
        __import__(import_name)
        print(f"✅ {name} is available")
        return True
    except ImportError as e:
        print(f"❌ {name} is missing: {e}")
        return False

def main():
    print("Checking dependencies for API systems...")
    print("=" * 50)
    
    # Required dependencies from the completion report
    dependencies = [
        ("redis", "redis"),
        ("pyjwt", "jwt"),
        ("authlib", "authlib"),
        ("flask-socketio", "flask_socketio"),
        ("graphene", "graphene"),
        ("flask-caching", "flask_caching"),
        ("flask", "flask"),
        ("flask-sqlalchemy", "flask_sqlalchemy"),
        ("werkzeug", "werkzeug"),
        ("sqlalchemy", "sqlalchemy"),
    ]
    
    missing_deps = []
    
    for dep_name, import_name in dependencies:
        if not check_dependency(dep_name, import_name):
            missing_deps.append(dep_name)
    
    print("\n" + "=" * 50)
    
    # Check specific authlib components
    print("Checking authlib components...")
    try:
        from authlib.integrations.sqla_oauth2 import OAuth2ClientMixin, OAuth2TokenMixin, OAuth2AuthorizationCodeMixin
        print("✅ OAuth2 mixins available")
    except ImportError as e:
        print(f"❌ OAuth2 mixins issue: {e}")
        missing_deps.append("authlib-oauth2-mixins")
    
    # Check Redis connectivity
    print("\nChecking Redis connectivity...")
    try:
        import redis
        # Try to connect to Redis (will fail if not running, but that's ok for now)
        print("✅ Redis library available")
    except ImportError:
        print("❌ Redis library not available")
        missing_deps.append("redis")
    
    # Check JWT functionality
    print("\nChecking JWT functionality...")
    try:
        import jwt
        # Test basic JWT encoding/decoding
        test_token = jwt.encode({"test": "data"}, "secret", algorithm="HS256")
        jwt.decode(test_token, "secret", algorithms=["HS256"])
        print("✅ JWT functionality working")
    except ImportError:
        print("❌ JWT library not available")
        missing_deps.append("pyjwt")
    except Exception as e:
        print(f"⚠️ JWT functionality issue: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("DEPENDENCY CHECK SUMMARY")
    print("=" * 50)
    
    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        print("\nTo install missing dependencies, run:")
        print(f"pip install {' '.join(missing_deps)}")
    else:
        print("✅ All dependencies are available")
    
    # Check configuration requirements
    print("\nChecking configuration requirements...")
    config_vars = [
        "REDIS_CACHE_URL",
        "JWT_SECRET_KEY",
        "OAUTH2_GOOGLE_CLIENT_ID",
        "OAUTH2_GOOGLE_CLIENT_SECRET",
        "API_CACHE_ENABLED",
        "API_VERSIONING_ENABLED",
        "WEBSOCKET_ENABLED",
    ]
    
    print("Required environment variables:")
    for var in config_vars:
        print(f"  - {var}")
    
    print(f"\nTotal dependencies checked: {len(dependencies)}")
    print(f"Missing dependencies: {len(missing_deps)}")
    
    return len(missing_deps) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
