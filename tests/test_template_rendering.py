#!/usr/bin/env python3
"""
Test script to diagnose Flask template rendering issues
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app import create_app
from flask import render_template

def test_template_rendering():
    """Test Flask template rendering system"""
    
    print("🔍 Testing Flask Template Rendering System")
    print("=" * 50)
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        # Test 1: Basic template rendering without variables
        print("✅ Test 1: Basic template rendering...")
        try:
            result = render_template('errors/404.html')
            print(f"   ✓ Basic template rendering successful")
            print(f"   ✓ Template length: {len(result)} characters")
        except Exception as e:
            print(f"   ❌ Basic template rendering failed: {e}")
            return False
        
        # Test 2: Template rendering with simple variables
        print("\n✅ Test 2: Template rendering with simple variables...")
        try:
            result = render_template('errors/404.html', test_var="test_value")
            print(f"   ✓ Template rendering with variables successful")
            print(f"   ✓ Template length: {len(result)} characters")
        except Exception as e:
            print(f"   ❌ Template rendering with variables failed: {e}")
            return False
        
        # Test 3: Template rendering with the problematic variable
        print("\n✅ Test 3: Template rendering with 'user_inbox' variable...")
        try:
            result = render_template('errors/404.html', user_inbox="test_value")
            print(f"   ✓ Template rendering with 'user_inbox' successful")
            print(f"   ✓ Template length: {len(result)} characters")
        except Exception as e:
            print(f"   ❌ Template rendering with 'user_inbox' failed: {e}")
            return False
        
        # Test 4: Test the actual inbox template
        print("\n✅ Test 4: Testing actual inbox template...")
        try:
            result = render_template('message/inbox.html', user_inbox=[], unread_count=0)
            print(f"   ✓ Inbox template rendering successful")
            print(f"   ✓ Template length: {len(result)} characters")
        except Exception as e:
            print(f"   ❌ Inbox template rendering failed: {e}")
            return False
        
        print("\n🎉 All template rendering tests passed!")
        return True

def test_flask_app_context():
    """Test Flask app context"""
    
    print("\n🔍 Testing Flask App Context")
    print("=" * 30)
    
    app = create_app()
    
    # Test app context
    with app.app_context():
        print("✅ App context created successfully")
        
        # Test template folder
        template_folder = app.template_folder
        print(f"✅ Template folder: {template_folder}")
        
        # Test if template exists
        inbox_template = os.path.join(template_folder, 'message', 'inbox.html')
        if os.path.exists(inbox_template):
            print(f"✅ Inbox template exists: {inbox_template}")
        else:
            print(f"❌ Inbox template missing: {inbox_template}")
            return False
    
    return True

if __name__ == '__main__':
    print("🚀 Starting Flask Template Rendering Diagnostics")
    print("=" * 60)
    
    success = True
    
    # Run tests
    if not test_flask_app_context():
        success = False
    
    if not test_template_rendering():
        success = False
    
    if success:
        print("\n🎯 All tests completed successfully!")
        print("📊 Flask template rendering system is working correctly")
    else:
        print("\n❌ Some tests failed. Flask template rendering system has issues.")
        sys.exit(1)
