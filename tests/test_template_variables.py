#!/usr/bin/env python3
"""
Test script to isolate template variable issues
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app import create_app
from flask import render_template

def test_template_variables():
    """Test different variable names with the template"""
    
    print("🔍 Testing Template Variable Names")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        # Test 1: Test with 'user_inbox' variable
        print("✅ Test 1: Testing with 'user_inbox' variable...")
        try:
            result = render_template('message/inbox.html', user_inbox=[], unread_count=0)
            print(f"   ✓ SUCCESS: Template rendered with 'user_inbox'")
            print(f"   ✓ Template length: {len(result)} characters")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
        
        # Test 2: Test with 'messages' variable
        print("\n✅ Test 2: Testing with 'messages' variable...")
        try:
            result = render_template('message/inbox.html', messages=[], unread_count=0)
            print(f"   ✓ SUCCESS: Template rendered with 'messages'")
            print(f"   ✓ Template length: {len(result)} characters")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
        
        # Test 3: Test with 'msgs' variable
        print("\n✅ Test 3: Testing with 'msgs' variable...")
        try:
            result = render_template('message/inbox.html', msgs=[], unread_count=0)
            print(f"   ✓ SUCCESS: Template rendered with 'msgs'")
            print(f"   ✓ Template length: {len(result)} characters")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
        
        # Test 4: Test with 'inbox_messages' variable
        print("\n✅ Test 4: Testing with 'inbox_messages' variable...")
        try:
            result = render_template('message/inbox.html', inbox_messages=[], unread_count=0)
            print(f"   ✓ SUCCESS: Template rendered with 'inbox_messages'")
            print(f"   ✓ Template length: {len(result)} characters")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
        
        # Test 5: Test with 'data' variable
        print("\n✅ Test 5: Testing with 'data' variable...")
        try:
            result = render_template('message/inbox.html', data=[], unread_count=0)
            print(f"   ✓ SUCCESS: Template rendered with 'data'")
            print(f"   ✓ Template length: {len(result)} characters")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")

def test_template_without_variables():
    """Test template rendering without variables"""
    
    print("\n🔍 Testing Template Without Variables")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        # Test template without any variables
        print("✅ Test: Template without variables...")
        try:
            result = render_template('message/inbox.html')
            print(f"   ✓ SUCCESS: Template rendered without variables")
            print(f"   ✓ Template length: {len(result)} characters")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")

def test_minimal_template():
    """Test with a minimal template"""
    
    print("\n🔍 Testing Minimal Template")
    print("=" * 30)
    
    app = create_app()
    
    with app.app_context():
        # Test with minimal template
        print("✅ Test: Minimal template...")
        try:
            result = render_template('message/inbox_standalone.html', user_inbox=[], unread_count=0)
            print(f"   ✓ SUCCESS: Minimal template rendered")
            print(f"   ✓ Template length: {len(result)} characters")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")

if __name__ == '__main__':
    print("🚀 Starting Template Variable Testing")
    print("=" * 50)
    
    test_template_variables()
    test_template_without_variables()
    test_minimal_template()
    
    print("\n🎯 Testing completed!")
