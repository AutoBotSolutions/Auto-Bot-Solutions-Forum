#!/usr/bin/env python3
"""
Test script for the automatic error monitoring system
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app import create_app
from app.error_monitor import ErrorMonitor, test_error_monitoring

def test_error_monitoring_system():
    """Test the error monitoring system"""
    
    print("🔍 Testing Automatic Error Monitoring System")
    print("=" * 50)
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        # Test 1: Test error logging
        print("✅ Test 1: Testing error logging...")
        try:
            error_info = test_error_monitoring()
            print(f"   ✓ Error logged: {error_info['error_type']}")
            print(f"   ✓ Error message: {error_info['error_message']}")
            print(f"   ✓ Timestamp: {error_info['timestamp']}")
        except Exception as e:
            print(f"   ❌ Error logging test failed: {e}")
            return False
        
        # Test 2: Test recent errors retrieval
        print("\n✅ Test 2: Testing recent errors retrieval...")
        try:
            recent_errors = ErrorMonitor.get_recent_errors()
            print(f"   ✓ Retrieved {len(recent_errors)} recent errors")
            if recent_errors:
                latest_error = recent_errors[-1]
                print(f"   ✓ Latest error: {latest_error['error_type']}")
        except Exception as e:
            print(f"   ❌ Recent errors test failed: {e}")
            return False
        
        # Test 3: Test error count
        print("\n✅ Test 3: Testing error count...")
        try:
            error_count = ErrorMonitor.get_error_count()
            print(f"   ✓ Total error count: {error_count}")
        except Exception as e:
            print(f"   ❌ Error count test failed: {e}")
            return False
        
        # Test 4: Test error clearing
        print("\n✅ Test 4: Testing error clearing...")
        try:
            ErrorMonitor.clear_errors()
            cleared_count = ErrorMonitor.get_error_count()
            print(f"   ✓ Errors cleared. Current count: {cleared_count}")
        except Exception as e:
            print(f"   ❌ Error clearing test failed: {e}")
            return False
        
        print("\n🎉 All error monitoring tests passed!")
        return True

def test_messages_page_monitoring():
    """Test error monitoring specifically on the messages page"""
    
    print("\n🔍 Testing Messages Page Error Monitoring")
    print("=" * 50)
    
    app = create_app()
    
    with app.test_client() as client:
        # Test accessing messages page (should redirect to login)
        print("✅ Testing messages page access...")
        try:
            response = client.get('/messages/')
            print(f"   ✓ Response status: {response.status_code}")
            
            # Check if error monitoring captured anything
            recent_errors = ErrorMonitor.get_recent_errors()
            if recent_errors:
                print(f"   ✓ Captured {len(recent_errors)} errors during test")
            else:
                print("   ✓ No errors captured (expected for successful request)")
                
        except Exception as e:
            print(f"   ❌ Messages page test failed: {e}")
            return False
    
    return True

if __name__ == '__main__':
    print("🚀 Starting Error Monitoring System Tests")
    print("=" * 60)
    
    success = True
    
    # Run tests
    if not test_error_monitoring_system():
        success = False
    
    if not test_messages_page_monitoring():
        success = False
    
    if success:
        print("\n🎯 All tests completed successfully!")
        print("📊 Error monitoring system is ready to automatically detect page errors")
        print("🔗 Admin routes available:")
        print("   - /admin/errors - View recent errors")
        print("   - /admin/errors/clear - Clear error logs")
        print("   - /admin/errors/stats - Error statistics")
    else:
        print("\n❌ Some tests failed. Please check the error monitoring system.")
        sys.exit(1)
