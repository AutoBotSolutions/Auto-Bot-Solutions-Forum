#!/usr/bin/env python3
"""
Debug the actual route issue to identify the difference between test and route context
"""

import sys
import os
import traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app import create_app
from flask import render_template, request
from flask_login import current_user

def debug_actual_route():
    """Debug the actual route that's failing"""
    print("🔍 DEBUGGING ACTUAL ROUTE")
    print("=" * 40)
    
    app = create_app()
    
    with app.test_client() as client:
        try:
            # Get the route function directly
            from app.message.routes import message_bp
            
            # Test the route function directly
            with app.test_request_context():
                # Mock current_user for testing
                from flask import g
                from flask_login import AnonymousUserMixin
                
                # Set up mock user
                class MockUser:
                    def __init__(self):
                        self.id = 1
                        self.is_authenticated = True
                
                # Try to call the route function directly
                try:
                    # Import the route function
                    from app.message.routes import inbox
                    
                    # Set up mock current_user
                    g.current_user = MockUser()
                    
                    # Call the route function
                    result = inbox()
                    print(f"✅ Route function returned: {type(result)}")
                    return True
                    
                except Exception as route_error:
                    print(f"❌ Route function failed: {route_error}")
                    print(f"❌ Traceback: {traceback.format_exc()}")
                    return False
                    
        except Exception as e:
            print(f"❌ Route debugging failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def debug_route_with_context():
    """Debug the route with proper Flask context"""
    print("\n🔍 DEBUGGING ROUTE WITH CONTEXT")
    print("=" * 45)
    
    app = create_app()
    
    # Test with actual HTTP request
    with app.test_client() as client:
        try:
            # Make actual request to the route
            response = client.get('/messages/')
            print(f"✅ Response status: {response.status_code}")
            
            if response.status_code == 302:
                print("✅ Route redirects to login (expected)")
                return True
            elif response.status_code == 500:
                print("❌ Route returns 500 error")
                print(f"❌ Response data: {response.data[:1000]}")
                return False
            else:
                print(f"✅ Route returns {response.status_code}")
                return True
                
        except Exception as e:
            print(f"❌ Route request failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def debug_error_monitoring_interference():
    """Debug if error monitoring system is interfering"""
    print("\n🔍 DEBUGGING ERROR MONITORING INTERFERENCE")
    print("=" * 55)
    
    # Test without error monitoring
    print("✅ Testing without error monitoring...")
    
    # Create app without error monitoring
    app = create_app()
    app.config['ERROR_MONITORING_ENABLED'] = False
    
    with app.test_request_context():
        try:
            result = render_template('message/inbox.html', messages=[], unread_count=0)
            print("✅ Template renders without error monitoring")
            return True
        except Exception as e:
            print(f"❌ Template fails without error monitoring: {e}")
            return False

def debug_flask_login_interference():
    """Debug if Flask-Login is interfering"""
    print("\n🔍 DEBUGGING FLASK-LOGIN INTERFERENCE")
    print("=" * 50)
    
    app = create_app()
    
    with app.test_request_context():
        try:
            # Test render_template with Flask-Login active
            result = render_template('message/inbox.html', messages=[], unread_count=0)
            print("✅ Template renders with Flask-Login active")
            return True
        except Exception as e:
            print(f"❌ Template fails with Flask-Login: {e}")
            return False

def debug_route_step_by_step():
    """Debug the route step by step"""
    print("\n🔍 DEBUGGING ROUTE STEP BY STEP")
    print("=" * 45)
    
    app = create_app()
    
    with app.test_request_context():
        try:
            # Step 1: Import current_user
            from flask_login import current_user
            print("✅ Step 1: Imported current_user")
            
            # Step 2: Check authentication
            if not current_user.is_authenticated:
                print("✅ Step 2: User not authenticated (expected)")
                return True
            else:
                print("❌ Step 2: User is authenticated (unexpected)")
                
        except Exception as e:
            print(f"❌ Step debugging failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def main():
    """Main debugging function"""
    print("🚀 ROUTE-SPECIFIC DEBUGGING")
    print("=" * 50)
    
    tests = [
        ("Actual Route", debug_actual_route),
        ("Route with Context", debug_route_with_context),
        ("Error Monitoring Interference", debug_error_monitoring_interference),
        ("Flask-Login Interference", debug_flask_login_interference),
        ("Route Step by Step", debug_route_step_by_step),
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
    print("🎯 ROUTE DEBUGGING SUMMARY")
    print(f"{'='*50}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    failed_tests = [name for name, result in results.items() if not result]
    
    if failed_tests:
        print(f"\n❌ FAILED TESTS: {', '.join(failed_tests)}")
        print("🔧 These areas need investigation")
        return False
    else:
        print(f"\n✅ ALL ROUTE TESTS PASSED")
        print("🎯 Route is working correctly")
        return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
