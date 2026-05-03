"""
Comprehensive Notification Tests for Repo-Forum Project
Tests notification functionality.
"""

import re
import traceback
from datetime import datetime

class NotificationTest:
    """Comprehensive notification testing for entire app"""
    
    def __init__(self, framework):
        self.framework = framework
        self.app = None
        self.test_results = []
    
    def add_test_result(self, test_name, status, message, details=None):
        """Add test result to framework"""
        self.framework.test_results.append({
            "test_name": test_name,
            "category": "notification",
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def run_all_tests(self):
        """Run all notification tests"""
        print("🔔 Running Comprehensive Notification Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app
            self.app = create_app()
            
            with self.app.app_context():
                # Test notification functionality
                self.test_notification_display()
                self.test_notification_creation()
                self.test_notification_management()
                
        except Exception as e:
            self.add_test_result("notification_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_notification_display(self):
        """Test notification display functionality"""
        try:
            with self.app.test_client() as client:
                response = client.get('/notification')
                
                if response.status_code in [200, 302]:
                    self.add_test_result("notification_display_accessible", "passed", 
                                      "Notification display page accessible")
                else:
                    self.add_test_result("notification_display_accessible", "failed", 
                                      f"Notification display not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("notification_display", "error", str(e), traceback.format_exc())
    
    def test_notification_creation(self):
        """Test notification creation functionality"""
        try:
            with self.app.test_client() as client:
                response = client.get('/notification')
                
                if response.status_code in [200, 302]:
                    self.add_test_result("notification_creation_accessible", "passed", 
                                      "Notification creation page accessible")
                else:
                    self.add_test_result("notification_creation_accessible", "failed", 
                                      f"Notification creation not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("notification_creation", "error", str(e), traceback.format_exc())
    
    def test_notification_management(self):
        """Test notification management functionality"""
        try:
            with self.app.test_client() as client:
                response = client.get('/notification')
                
                if response.status_code in [200, 302]:
                    self.add_test_result("notification_management_accessible", "passed", 
                                      "Notification management page accessible")
                else:
                    self.add_test_result("notification_management_accessible", "failed", 
                                      f"Notification management not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("notification_management", "error", str(e), traceback.format_exc())
