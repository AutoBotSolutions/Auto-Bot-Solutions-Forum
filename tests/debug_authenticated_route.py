#!/usr/bin/env python3
"""
Debug the route with authenticated user context to reproduce the actual error
"""

import sys
import os
import traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app import create_app
from flask import render_template, request
from flask_login import current_user

def debug_authenticated_route():
    """Debug the route with authenticated user context"""
    print("🔍 DEBUGGING AUTHENTICATED ROUTE")
    print("=" * 45)
    
    app = create_app()
    
    with app.test_request_context():
        try:
            # Mock authenticated user
            from flask import g
            from flask_login import AnonymousUserMixin
            
            class MockUser:
                def __init__(self):
                    self.id = 1
                    self.is_authenticated = True
                    self.username = "testuser"
            
            # Set up mock authenticated user
            g.current_user = MockUser()
            
            # Import the route function
            from app.message.routes import inbox
            
            # Call the route function with authenticated user
            try:
                result = inbox()
                print(f"✅ Route function returned: {type(result)}")
                return True
                
            except Exception as route_error:
                print(f"❌ Route function failed with authenticated user: {route_error}")
                print(f"❌ Traceback: {traceback.format_exc()}")
                return False
                
        except Exception as e:
            print(f"❌ Authenticated route debugging failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def debug_template_rendering_with_auth():
    """Debug template rendering with authenticated user"""
    print("\n🔍 DEBUGGING TEMPLATE RENDERING WITH AUTH")
    print("=" * 55)
    
    app = create_app()
    
    with app.test_request_context():
        try:
            # Mock authenticated user
            from flask import g
            
            class MockUser:
                def __init__(self):
                    self.id = 1
                    self.is_authenticated = True
            
            g.current_user = MockUser()
            
            # Test template rendering with authenticated context
            result = render_template('message/inbox.html', messages=[], unread_count=0)
            print("✅ Template renders with authenticated user")
            return True
            
        except Exception as e:
            print(f"❌ Template fails with authenticated user: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def debug_database_query_with_auth():
    """Debug database query with authenticated user"""
    print("\n🔍 DEBUGGING DATABASE QUERY WITH AUTH")
    print("=" * 50)
    
    app = create_app()
    
    with app.test_request_context():
        try:
            # Mock authenticated user
            from flask import g
            from app.models import User
            
            class MockUser:
                def __init__(self):
                    self.id = 1
                    self.is_authenticated = True
            
            g.current_user = MockUser()
            
            # Test database query
            from app.models import Message
            messages = Message.query.filter_by(receiver_id=1).order_by(Message.created_at.desc()).all()
            unread_count = Message.query.filter_by(receiver_id=1, is_read=False).count()
            
            print(f"✅ Database query successful: {len(messages)} messages, {unread_count} unread")
            
            # Test template rendering with real data
            result = render_template('message/inbox.html', messages=messages, unread_count=unread_count)
            print("✅ Template renders with real database data")
            return True
            
        except Exception as e:
            print(f"❌ Database query or template rendering failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def debug_route_components():
    """Debug each component of the route separately"""
    print("\n🔍 DEBUGGING ROUTE COMPONENTS")
    print("=" * 45)
    
    app = create_app()
    
    with app.test_request_context():
        try:
            # Mock authenticated user
            from flask import g
            
            class MockUser:
                def __init__(self):
                    self.id = 1
                    self.is_authenticated = True
            
            g.current_user = MockUser()
            
            # Component 1: Import statements
            from app.error_system import monitor_error
            print("✅ Component 1: Import statements successful")
            
            # Component 2: Database queries
            from app.models import Message
            user_inbox = Message.query.filter_by(receiver_id=1).order_by(Message.created_at.desc()).all()
            unread_count = Message.query.filter_by(receiver_id=1, is_read=False).count()
            print(f"✅ Component 2: Database queries successful ({len(user_inbox)} messages)")
            
            # Component 3: Template variables
            template_vars = {
                'user_inbox': user_inbox,
                'unread_count': unread_count,
                'template_name': 'message/inbox.html'
            }
            print("✅ Component 3: Template variables prepared")
            
            # Component 4: Template rendering
            result = render_template('message/inbox.html', messages=user_inbox, unread_count=unread_count)
            print("✅ Component 4: Template rendering successful")
            
            return True
            
        except Exception as e:
            print(f"❌ Route component failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def main():
    """Main debugging function"""
    print("🚀 AUTHENTICATED ROUTE DEBUGGING")
    print("=" * 60)
    
    tests = [
        ("Authenticated Route", debug_authenticated_route),
        ("Template Rendering with Auth", debug_template_rendering_with_auth),
        ("Database Query with Auth", debug_database_query_with_auth),
        ("Route Components", debug_route_components),
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
    
    print(f"\n{'='*60}")
    print("🎯 AUTHENTICATED ROUTE DEBUGGING SUMMARY")
    print(f"{'='*60}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    failed_tests = [name for name, result in results.items() if not result]
    
    if failed_tests:
        print(f"\n❌ FAILED TESTS: {', '.join(failed_tests)}")
        print("🔧 These areas need investigation")
        return False
    else:
        print(f"\n✅ ALL AUTHENTICATED ROUTE TESTS PASSED")
        print("🎯 Route is working correctly with authenticated users")
        return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
