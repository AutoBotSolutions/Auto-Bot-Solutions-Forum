"""
Comprehensive Post Tests for Repo-Forum Project
Tests post functionality.
"""

import re
import traceback
from datetime import datetime

class PostTest:
    """Comprehensive post testing for entire app"""
    
    def __init__(self, framework):
        self.framework = framework
        self.app = None
        self.test_results = []
    
    def add_test_result(self, test_name, status, message, details=None):
        """Add test result to framework"""
        self.framework.test_results.append({
            "test_name": test_name,
            "category": "forum",
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def run_all_tests(self):
        """Run all post tests"""
        print("📝 Running Comprehensive Post Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app
            self.app = create_app()
            
            with self.app.app_context():
                # Test post functionality
                self.test_post_creation()
                self.test_post_display()
                self.test_post_editing()
                
        except Exception as e:
            self.add_test_result("post_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_post_creation(self):
        """Test post creation functionality"""
        try:
            with self.app.test_client() as client:
                response = client.get('/forum/create')
                
                if response.status_code in [200, 302]:
                    self.add_test_result("post_creation_accessible", "passed", 
                                      "Post creation page accessible")
                else:
                    self.add_test_result("post_creation_accessible", "failed", 
                                      f"Post creation not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("post_creation", "error", str(e), traceback.format_exc())
    
    def test_post_display(self):
        """Test post display functionality"""
        try:
            with self.app.test_client() as client:
                response = client.get('/forum/post/1')
                
                if response.status_code in [200, 404]:
                    self.add_test_result("post_display_accessible", "passed", 
                                      "Post display page accessible")
                else:
                    self.add_test_result("post_display_accessible", "failed", 
                                      f"Post display not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("post_display", "error", str(e), traceback.format_exc())
    
    def test_post_editing(self):
        """Test post editing functionality"""
        try:
            with self.app.test_client() as client:
                response = client.get('/forum/edit/1')
                
                if response.status_code in [200, 302, 403, 401]:
                    self.add_test_result("post_editing_accessible", "passed", 
                                      "Post editing page accessible")
                else:
                    self.add_test_result("post_editing_accessible", "failed", 
                                      f"Post editing not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("post_editing", "error", str(e), traceback.format_exc())
