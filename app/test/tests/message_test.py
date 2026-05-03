"""
Comprehensive Message Tests for Repo-Forum Project
Tests messaging functionality.
"""

import re
import traceback
from datetime import datetime

class MessageTest:
    """Comprehensive message testing for entire app"""
    
    def __init__(self, framework):
        self.framework = framework
        self.app = None
        self.test_results = []
    
    def add_test_result(self, test_name, status, message, details=None):
        """Add test result to framework"""
        self.framework.test_results.append({
            "test_name": test_name,
            "category": "message",
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def run_all_tests(self):
        """Run all message tests"""
        print("📧 Running Comprehensive Message Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app
            self.app = create_app()
            
            with self.app.app_context():
                # Test message functionality
                self.test_message_sending()
                self.test_message_display()
                self.test_message_inbox()
                
        except Exception as e:
            self.add_test_result("message_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_message_sending(self):
        """Test message sending functionality"""
        try:
            with self.app.test_client() as client:
                response = client.get('/message/new')
                
                if response.status_code in [200, 302]:
                    self.add_test_result("message_sending_accessible", "passed", 
                                      "Message sending page accessible")
                else:
                    self.add_test_result("message_sending_accessible", "failed", 
                                      f"Message sending not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("message_sending", "error", str(e), traceback.format_exc())
    
    def test_message_display(self):
        """Test message display functionality"""
        try:
            with self.app.test_client() as client:
                response = client.get('/message/inbox')
                
                if response.status_code in [200, 302]:
                    self.add_test_result("message_display_accessible", "passed", 
                                      "Message display page accessible")
                else:
                    self.add_test_result("message_display_accessible", "failed", 
                                      f"Message display not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("message_display", "error", str(e), traceback.format_exc())
    
    def test_message_inbox(self):
        """Test message inbox functionality"""
        try:
            with self.app.test_client() as client:
                response = client.get('/message/inbox')
                
                if response.status_code in [200, 302]:
                    self.add_test_result("message_inbox_accessible", "passed", 
                                      "Message inbox page accessible")
                else:
                    self.add_test_result("message_inbox_accessible", "failed", 
                                      f"Message inbox not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("message_inbox", "error", str(e), traceback.format_exc())
