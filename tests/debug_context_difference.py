#!/usr/bin/env python3
"""
Debug the difference between working test context and failing route context
"""

import sys
import os
import traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app import create_app
from flask import render_template, session
from flask_login import current_user, login_user

def debug_working_context():
    """Debug the working context (template rendering in isolation)"""
    print("🔍 DEBUGGING WORKING CONTEXT")
    print("=" * 40)
    
    app = create_app()
    
    with app.test_request_context():
        try:
            # This is the working context from previous tests
            print("✅ Working context: test_request_context with anonymous user")
            result = render_template('message/inbox.html', messages=[], unread_count=0)
            print("✅ Template renders successfully in working context")
            return True
        except Exception as e:
            print(f"❌ Working context failed: {e}")
            return False

def debug_failing_context():
    """Debug the failing context (authenticated user in route)"""
    print("\n🔍 DEBUGGING FAILING CONTEXT")
    print("=" * 40)
    
    app = create_app()
    
    with app.test_client() as client:
        try:
            # Simulate the failing context: authenticated user accessing route
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
            
            # Now test the messages route (this is where it fails)
            response = client.get('/messages/')
            print(f"❌ Failing context: messages route with authenticated user")
            print(f"❌ Status: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ Failing context crashed: {e}")
            return False

def debug_simulated_authenticated_context():
    """Debug simulated authenticated context without route"""
    print("\n🔍 DEBUGGING SIMULATED AUTHENTICATED CONTEXT")
    print("=" * 55)
    
    app = create_app()
    
    with app.test_request_context():
        try:
            # Simulate authenticated user
            from app.models import User
            admin_user = User.query.filter_by(username='admin').first()
            login_user(admin_user)
            
            print(f"✅ Simulated authenticated context: {current_user.username}")
            print(f"✅ Is authenticated: {current_user.is_authenticated}")
            
            # Test template rendering in this context
            result = render_template('message/inbox.html', messages=[], unread_count=0)
            print("✅ Template renders successfully in simulated authenticated context")
            return True
            
        except Exception as e:
            print(f"❌ Simulated authenticated context failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def debug_route_function_directly():
    """Debug the route function directly"""
    print("\n🔍 DEBUGGING ROUTE FUNCTION DIRECTLY")
    print("=" * 45)
    
    app = create_app()
    
    with app.test_request_context():
        try:
            # Simulate authenticated user
            from app.models import User
            admin_user = User.query.filter_by(username='admin').first()
            login_user(admin_user)
            
            # Import and call the route function directly
            from app.message.routes import inbox
            
            print(f"✅ Calling route function directly with authenticated user")
            result = inbox()
            print("✅ Route function executes successfully")
            return True
            
        except Exception as e:
            print(f"❌ Route function failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def debug_route_function_with_client():
    """Debug the route function with test client"""
    print("\n🔍 DEBUGGING ROUTE FUNCTION WITH TEST CLIENT")
    print("=" * 55)
    
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
            
            # Now call the route function directly through app context
            with app.test_request_context():
                from app.message.routes import inbox
                
                # Copy session from client to app context
                with client.session_transaction() as sess:
                    session_data = dict(sess)
                
                for key, value in session_data.items():
                    session[key] = value
                
                print(f"✅ Calling route function with client session")
                result = inbox()
                print("✅ Route function executes successfully with client session")
                return True
                
        except Exception as e:
            print(f"❌ Route function with client failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def main():
    """Main debug function"""
    print("🚀 CONTEXT DIFFERENCE DEBUGGING")
    print("=" * 50)
    
    tests = [
        ("Working Context", debug_working_context),
        ("Failing Context", debug_failing_context),
        ("Simulated Authenticated Context", debug_simulated_authenticated_context),
        ("Route Function Directly", debug_route_function_directly),
        ("Route Function with Client", debug_route_function_with_client),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            results[test_name] = False
    
    print(f"\n{'='*50}")
    print("🎯 CONTEXT DIFFERENCE DEBUGGING SUMMARY")
    print(f"{'='*50}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    failed_tests = [name for name, result in results.items() if not result]
    
    if failed_tests:
        print(f"\n❌ FAILED TESTS: {', '.join(failed_tests)}")
        print("🔧 These areas need investigation and fixing")
        return False
    else:
        print(f"\n✅ ALL TESTS PASSED")
        print("🎯 No context difference detected")
        return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
