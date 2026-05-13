#!/usr/bin/env python3
"""
Debug the login process and Flask-Login session management
"""

import sys
import os
import traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app import create_app
from flask import session
from flask_login import login_user, logout_user, current_user

def debug_flask_login_config():
    """Debug Flask-Login configuration"""
    print("🔍 DEBUGGING FLASK-LOGIN CONFIGURATION")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            from app import login_manager
            
            print(f"✅ LoginManager initialized: {login_manager}")
            print(f"✅ LoginManager app: {login_manager.app}")
            print(f"✅ LoginManager session_protection: {getattr(login_manager, 'session_protection', 'not set')}")
            print(f"✅ LoginManager login_view: {getattr(login_manager, 'login_view', 'not set')}")
            
            # Check user loader
            print(f"✅ User loader function: {login_manager._user_callback}")
            
            return True
            
        except Exception as e:
            print(f"❌ Flask-Login config debug failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def debug_user_model():
    """Debug User model and authentication methods"""
    print("\n🔍 DEBUGGING USER MODEL")
    print("=" * 35)
    
    app = create_app()
    
    with app.app_context():
        try:
            from app.models import User
            
            # Get admin user
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("❌ Admin user not found")
                return False
            
            print(f"✅ Admin user found: {admin_user.username}")
            print(f"✅ User ID: {admin_user.id}")
            print(f"✅ User is_authenticated: {admin_user.is_authenticated}")
            print(f"✅ User is_active: {admin_user.is_active}")
            print(f"✅ User can_login: {admin_user.can_login()}")
            print(f"✅ User is_banned: {admin_user.is_banned}")
            print(f"✅ User is_suspended: {admin_user.is_suspended}")
            print(f"✅ User is_verified: {admin_user.is_verified}")
            
            # Test password check
            print(f"✅ Password check (admin123): {admin_user.check_password('admin123')}")
            
            return True
            
        except Exception as e:
            print(f"❌ User model debug failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def debug_login_process():
    """Debug the complete login process"""
    print("\n🔍 DEBUGGING LOGIN PROCESS")
    print("=" * 40)
    
    app = create_app()
    
    with app.test_client() as client:
        try:
            # Get login page
            response = client.get('/auth/login')
            print(f"✅ Login page status: {response.status_code}")
            
            # Get CSRF token
            csrf_token = None
            if b'csrf_token' in response.data:
                import re
                csrf_match = re.search(rb'name="csrf_token".*?value="([^"]+)"', response.data)
                if csrf_match:
                    csrf_token = csrf_match.group(1).decode('utf-8')
                    print(f"✅ CSRF token extracted: {csrf_token[:20]}...")
            
            if not csrf_token:
                print("❌ Could not extract CSRF token")
                return False
            
            # Test login with correct credentials
            login_data = {
                'username': 'admin',
                'password': 'admin123',
                'csrf_token': csrf_token
            }
            
            response = client.post('/auth/login', data=login_data, follow_redirects=False)
            print(f"✅ Login POST status: {response.status_code}")
            
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                print(f"✅ Redirect location: {location}")
                
                # Follow redirect
                response = client.get(location)
                print(f"✅ Final page status: {response.status_code}")
                
                # Check if user is logged in
                with app.test_request_context():
                    from flask_login import current_user
                    print(f"✅ Current user after login: {current_user}")
                    print(f"✅ Is authenticated: {current_user.is_authenticated}")
                
                return response.status_code == 200
            else:
                print(f"❌ Login failed - status: {response.status_code}")
                print(f"❌ Response: {response.data[:500]}")
                return False
                
        except Exception as e:
            print(f"❌ Login process debug failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def debug_session_management():
    """Debug session management"""
    print("\n🔍 DEBUGGING SESSION MANAGEMENT")
    print("=" * 45)
    
    app = create_app()
    
    with app.test_client() as client:
        try:
            # Login first
            response = client.get('/auth/login')
            import re
            csrf_match = re.search(rb'name="csrf_token".*?value="([^"]+)"', response.data)
            csrf_token = csrf_match.group(1).decode('utf-8') if csrf_match else None
            
            login_data = {
                'username': 'admin',
                'password': 'admin123',
                'csrf_token': csrf_token
            }
            
            response = client.post('/auth/login', data=login_data)
            
            # Check session after login
            with client.session_transaction() as sess:
                print(f"✅ Session keys: {list(sess.keys())}")
                print(f"✅ User ID in session: {sess.get('user_id')}")
                print(f"✅ Fresh flag: {sess.get('_fresh')}")
                print(f"✅ Session data: {dict(sess)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Session management debug failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def debug_messages_with_login():
    """Test messages page after login"""
    print("\n🔍 DEBUGGING MESSAGES PAGE WITH LOGIN")
    print("=" * 50)
    
    app = create_app()
    
    with app.test_client() as client:
        try:
            # Login first
            response = client.get('/auth/login')
            import re
            csrf_match = re.search(rb'name="csrf_token".*?value="([^"]+)"', response.data)
            csrf_token = csrf_match.group(1).decode('utf-8') if csrf_match else None
            
            login_data = {
                'username': 'admin',
                'password': 'admin123',
                'csrf_token': csrf_token
            }
            
            # Login
            response = client.post('/auth/login', data=login_data)
            
            # Test messages page
            response = client.get('/messages/')
            print(f"✅ Messages page status after login: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Messages page loads successfully after login")
                response_text = response.data.decode('utf-8')
                if 'INBOX' in response_text:
                    print("✅ Messages page contains expected content")
                    return True
                else:
                    print("❌ Messages page missing expected content")
                    return False
            else:
                print(f"❌ Messages page failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Messages page debug failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def main():
    """Main debug function"""
    print("🚀 COMPREHENSIVE LOGIN DEBUGGING")
    print("=" * 60)
    
    tests = [
        ("Flask-Login Configuration", debug_flask_login_config),
        ("User Model", debug_user_model),
        ("Login Process", debug_login_process),
        ("Session Management", debug_session_management),
        ("Messages Page with Login", debug_messages_with_login),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*25} {test_name} {'='*25}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            results[test_name] = False
    
    print(f"\n{'='*60}")
    print("🎯 LOGIN DEBUGGING SUMMARY")
    print(f"{'='*60}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    failed_tests = [name for name, result in results.items() if not result]
    
    if failed_tests:
        print(f"\n❌ FAILED TESTS: {', '.join(failed_tests)}")
        print("🔧 These areas need investigation and fixing")
        return False
    else:
        print(f"\n✅ ALL LOGIN TESTS PASSED")
        print("🎯 Login and authentication system working correctly")
        return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
