#!/usr/bin/env python3
"""
Systematic debugging script for template rendering issues
"""

import sys
import os
import traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app import create_app
from flask import render_template, request
from flask_login import current_user

def debug_flask_app():
    """Debug Flask app configuration and setup"""
    print("🔍 DEBUGGING FLASK APP CONFIGURATION")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        print(f"✅ Flask app created: {app}")
        print(f"✅ Template folder: {app.template_folder}")
        print(f"✅ Debug mode: {app.debug}")
        print(f"✅ Testing mode: {app.testing}")
        
        # Check template folder exists
        template_path = app.template_folder
        if os.path.exists(template_path):
            print(f"✅ Template folder exists: {template_path}")
        else:
            print(f"❌ Template folder missing: {template_path}")
            return False
        
        # Check message template exists
        inbox_template = os.path.join(template_path, 'message', 'inbox.html')
        if os.path.exists(inbox_template):
            print(f"✅ Inbox template exists: {inbox_template}")
        else:
            print(f"❌ Inbox template missing: {inbox_template}")
            return False
        
        # Check base template exists
        base_template = os.path.join(template_path, 'base.html')
        if os.path.exists(base_template):
            print(f"✅ Base template exists: {base_template}")
        else:
            print(f"❌ Base template missing: {base_template}")
            return False
        
        return True

def debug_template_syntax():
    """Debug template syntax and structure"""
    print("\n🔍 DEBUGGING TEMPLATE SYNTAX")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        try:
            from jinja2 import Environment, FileSystemLoader
            template_path = app.template_folder
            env = Environment(loader=FileSystemLoader(template_path))
            
            # Test template compilation
            template = env.get_template('message/inbox.html')
            print("✅ Template compiles successfully")
            
            # Test template rendering with minimal context
            try:
                result = template.render(messages=[], unread_count=0)
                print("✅ Template renders with minimal context")
                print(f"✅ Rendered length: {len(result)} characters")
            except Exception as render_error:
                print(f"❌ Template rendering failed: {render_error}")
                print(f"❌ Traceback: {traceback.format_exc()}")
                return False
                
        except Exception as template_error:
            print(f"❌ Template compilation failed: {template_error}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False
    
    return True

def debug_flask_render_template():
    """Debug Flask's render_template function"""
    print("\n🔍 DEBUGGING FLASK RENDER_TEMPLATE")
    print("=" * 45)
    
    app = create_app()
    
    with app.test_request_context():
        try:
            # Test render_template with different variable names
            test_cases = [
                {'messages': [], 'unread_count': 0},
                {'user_inbox': [], 'unread_count': 0},
                {'msgs': [], 'unread_count': 0},
                {'data': [], 'unread_count': 0},
                {'items': [], 'unread_count': 0},
            ]
            
            for i, context in enumerate(test_cases):
                print(f"\n✅ Test case {i+1}: {list(context.keys())}")
                try:
                    result = render_template('message/inbox.html', **context)
                    print(f"   ✓ SUCCESS: Rendered with {list(context.keys())}")
                    print(f"   ✓ Length: {len(result)} characters")
                except Exception as e:
                    print(f"   ❌ FAILED: {e}")
                    print(f"   ❌ Context: {context}")
                    print(f"   ❌ Traceback: {traceback.format_exc()}")
                    return False
                    
        except Exception as e:
            print(f"❌ Flask render_template failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False
    
    return True

def debug_minimal_template():
    """Debug with minimal template"""
    print("\n🔍 DEBUGGING MINIMAL TEMPLATE")
    print("=" * 35)
    
    app = create_app()
    
    with app.test_request_context():
        try:
            # Test with standalone template
            result = render_template('message/inbox_standalone.html', messages=[], unread_count=0)
            print("✅ Minimal template renders successfully")
            print(f"✅ Length: {len(result)} characters")
            return True
        except Exception as e:
            print(f"❌ Minimal template failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def debug_template_inheritance():
    """Debug template inheritance issues"""
    print("\n🔍 DEBUGGING TEMPLATE INHERITANCE")
    print("=" * 40)
    
    app = create_app()
    
    with app.test_request_context():
        try:
            # Test base template alone
            result = render_template('base.html')
            print("✅ Base template renders successfully")
            print(f"✅ Base template length: {len(result)} characters")
            
            # Test extending base template
            result = render_template('message/inbox.html', messages=[], unread_count=0)
            print("✅ Extended template renders successfully")
            print(f"✅ Extended template length: {len(result)} characters")
            return True
            
        except Exception as e:
            print(f"❌ Template inheritance failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def debug_route_context():
    """Debug route context and request handling"""
    print("\n🔍 DEBUGGING ROUTE CONTEXT")
    print("=" * 35)
    
    app = create_app()
    
    # Test with simulated route context
    with app.test_client() as client:
        try:
            # Test the actual route
            response = client.get('/messages/')
            print(f"✅ Route response status: {response.status_code}")
            
            if response.status_code == 302:
                print("✅ Route redirects to login (expected)")
                return True
            elif response.status_code == 200:
                print("✅ Route renders successfully")
                return True
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                print(f"❌ Response data: {response.data[:500]}")
                return False
                
        except Exception as e:
            print(f"❌ Route context failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def main():
    """Main debugging function"""
    print("🚀 SYSTEMATIC TEMPLATE DEBUGGING")
    print("=" * 60)
    
    tests = [
        ("Flask App Configuration", debug_flask_app),
        ("Template Syntax", debug_template_syntax),
        ("Flask render_template", debug_flask_render_template),
        ("Minimal Template", debug_minimal_template),
        ("Template Inheritance", debug_template_inheritance),
        ("Route Context", debug_route_context),
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
    print("🎯 DEBUGGING SUMMARY")
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
        print(f"\n✅ ALL TESTS PASSED")
        print("🎯 Template rendering system is working correctly")
        return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
