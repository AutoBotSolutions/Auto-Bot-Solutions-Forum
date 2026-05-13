#!/usr/bin/env python3
"""
Test the messages page with simulated authenticated user to verify TypeError is resolved
"""

import sys
import os
import traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app import create_app
from flask import render_template, request
from flask_login import login_user, logout_user, current_user

def test_messages_with_authenticated_user():
    """Test messages page with properly authenticated user"""
    print("🔍 TESTING MESSAGES PAGE WITH AUTHENTICATED USER")
    print("=" * 60)
    
    app = create_app()
    
    with app.test_request_context():
        try:
            # Get admin user from database
            from app.models import User
            admin_user = User.query.filter_by(username='admin').first()
            
            if not admin_user:
                print("❌ Admin user not found")
                return False
            
            print(f"✅ Found admin user: {admin_user.username} (ID: {admin_user.id})")
            
            # Simulate login
            with app.test_client() as client:
                # Login the user
                with client.session_transaction() as sess:
                    sess['user_id'] = admin_user.id
                    sess['_fresh'] = True
                
                # Test the messages route
                response = client.get('/messages/')
                print(f"✅ Messages route response status: {response.status_code}")
                
                if response.status_code == 200:
                    print("✅ Messages page renders successfully with authenticated user")
                    print(f"✅ Response length: {len(response.data)} characters")
                    
                    # Check if response contains expected content
                    response_text = response.data.decode('utf-8')
                    if 'INBOX' in response_text:
                        print("✅ Response contains expected content")
                    else:
                        print("❌ Response missing expected content")
                        return False
                    
                    return True
                elif response.status_code == 302:
                    print("❌ Still redirecting to login - authentication not working")
                    return False
                else:
                    print(f"❌ Unexpected status code: {response.status_code}")
                    print(f"❌ Response data: {response.data[:500]}")
                    return False
                    
        except Exception as e:
            print(f"❌ Test failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def test_template_rendering_with_auth():
    """Test template rendering directly with authenticated user"""
    print("\n🔍 TESTING TEMPLATE RENDERING WITH AUTHENTICATED USER")
    print("=" * 65)
    
    app = create_app()
    
    with app.test_request_context():
        try:
            # Get admin user
            from app.models import User
            admin_user = User.query.filter_by(username='admin').first()
            
            if not admin_user:
                print("❌ Admin user not found")
                return False
            
            # Simulate authentication
            from flask_login import login_user
            login_user(admin_user)
            
            print(f"✅ User authenticated: {current_user.username}")
            print(f"✅ User is_authenticated: {current_user.is_authenticated}")
            
            # Get messages for user
            from app.models import Message
            user_inbox = Message.query.filter_by(receiver_id=admin_user.id).order_by(Message.created_at.desc()).all()
            unread_count = Message.query.filter_by(receiver_id=admin_user.id, is_read=False).count()
            
            print(f"✅ Found {len(user_inbox)} messages, {unread_count} unread")
            
            # Render template
            result = render_template('message/inbox.html', messages=user_inbox, unread_count=unread_count)
            print("✅ Template renders successfully with authenticated user")
            print(f"✅ Template length: {len(result)} characters")
            
            return True
            
        except Exception as e:
            print(f"❌ Template rendering failed: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return False

def main():
    """Main test function"""
    print("🚀 TESTING MESSAGES PAGE WITH AUTHENTICATION")
    print("=" * 70)
    
    tests = [
        ("Messages Page with Authenticated User", test_messages_with_authenticated_user),
        ("Template Rendering with Authenticated User", test_template_rendering_with_auth),
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
    
    print(f"\n{'='*70}")
    print("🎯 AUTHENTICATION TESTING SUMMARY")
    print(f"{'='*70}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    failed_tests = [name for name, result in results.items() if not result]
    
    if failed_tests:
        print(f"\n❌ FAILED TESTS: {', '.join(failed_tests)}")
        print("🔧 These areas need investigation")
        return False
    else:
        print(f"\n✅ ALL AUTHENTICATION TESTS PASSED")
        print("🎯 Messages page works correctly with authenticated users")
        return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
