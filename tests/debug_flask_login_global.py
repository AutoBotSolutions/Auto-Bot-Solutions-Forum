#!/usr/bin/env python3
"""
Debug global Flask-Login interference issues
"""

import sys
import os
import traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app import create_app
from flask import render_template

def debug_global_flask_login_interference():
    """Debug if Flask-Login is globally interfering with render_template"""
    print("🔍 DEBUGGING GLOBAL FLASK-LOGIN INTERFERENCE")
    print("=" * 60)
    
    app = create_app()
    
    with app.test_request_context():
        try:
            # Test render_template in isolation
            print("✅ Testing render_template in isolation...")
            result = render_template('message/inbox.html', messages=[], unread_count=0)
            print("✅ render_template works in isolation")
            
            # Test with current_user context
            from flask_login import current_user
            print(f"✅ Current user in context: {current_user}")
            print(f"✅ Is authenticated: {current_user.is_authenticated}")
            
            # Test render_template with current_user context
            print("✅ Testing render_template with current_user context...")
            result = render_template('message/inbox.html', messages=[], unread_count=0)
            print("✅ render_template works with current_user context")
            
            return True
            
        except Exception as e:
            print(f"❌ Global Flask-Login interference detected: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def debug_flask_login_middleware():
    """Debug if there's Flask-Login middleware interfering"""
    print("\n🔍 DEBUGGING FLASK-LOGIN MIDDLEWARE")
    print("=" * 45)
    
    app = create_app()
    
    # Check Flask-Login configuration
    from app import login_manager
    print(f"✅ LoginManager: {login_manager}")
    print(f"✅ LoginManager app: {login_manager.app}")
    print(f"✅ Session protection: {getattr(login_manager, 'session_protection', 'not set')}")
    
    # Check if there are any global request hooks
    print(f"✅ App before_request hooks: {len(app.before_request_funcs)}")
    print(f"✅ App after_request hooks: {len(app.after_request_funcs)}")
    print(f"✅ App teardown_request hooks: {len(app.teardown_request_funcs)}")
    print(f"✅ App teardown_appcontext hooks: {len(app.teardown_appcontext_funcs)}")
    
    return True

def debug_render_template_directly():
    """Debug render_template function directly"""
    print("\n🔍 DEBUGGING RENDER_TEMPLATE DIRECTLY")
    print("=" * 50)
    
    app = create_app()
    
    with app.test_request_context():
        try:
            # Get the render_template function
            from flask import render_template
            print(f"✅ render_template function: {render_template}")
            print(f"✅ render_template module: {render_template.__module__}")
            
            # Check if render_template has been monkey-patched
            import flask
            print(f"✅ Flask render_template: {flask.render_template}")
            print(f"✅ Same function: {render_template is flask.render_template}")
            
            # Test with different variable names
            test_cases = [
                {'messages': [], 'unread_count': 0},
                {'msgs': [], 'unread_count': 0},
                {'data': [], 'unread_count': 0},
                {'items': [], 'unread_count': 0},
            ]
            
            for i, context in enumerate(test_cases):
                print(f"✅ Test case {i+1}: {list(context.keys())}")
                try:
                    result = render_template('message/inbox.html', **context)
                    print(f"   ✓ SUCCESS")
                except Exception as e:
                    print(f"   ❌ FAILED: {e}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Direct render_template debug failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def debug_template_without_flask_login():
    """Debug template rendering without Flask-Login"""
    print("\n🔍 DEBUGGING TEMPLATE WITHOUT FLASK-LOGIN")
    print("=" * 55)
    
    # Create a minimal app without Flask-Login
    from flask import Flask
    minimal_app = Flask(__name__)
    minimal_app.template_folder = '/home/robbie/Desktop/repo-forum/app/templates'
    
    with minimal_app.test_request_context():
        try:
            from flask import render_template
            result = render_template('message/inbox.html', messages=[], unread_count=0)
            print("✅ Template renders without Flask-Login")
            return True
        except Exception as e:
            print(f"❌ Template fails without Flask-Login: {e}")
            return False

def main():
    """Main debug function"""
    print("🚀 GLOBAL FLASK-LOGIN INTERFERENCE DEBUGGING")
    print("=" * 70)
    
    tests = [
        ("Global Flask-Login Interference", debug_global_flask_login_interference),
        ("Flask-Login Middleware", debug_flask_login_middleware),
        ("Render Template Directly", debug_render_template_directly),
        ("Template Without Flask-Login", debug_template_without_flask_login),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*30} {test_name} {'='*30}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            results[test_name] = False
    
    print(f"\n{'='*70}")
    print("🎯 GLOBAL FLASK-LOGIN DEBUGGING SUMMARY")
    print(f"{'='*70}")
    
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
        print("🎯 No global Flask-Login interference detected")
        return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
