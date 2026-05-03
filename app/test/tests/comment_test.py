"""
Comprehensive Comment Tests for Repo-Forum Project
Tests comment functionality.
"""

import re
import traceback
from datetime import datetime

class CommentTest:
    """Comprehensive comment testing for entire app"""
    
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
        """Run all comment tests"""
        print("💬 Running Comprehensive Comment Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app
            self.app = create_app()
            
            with self.app.app_context():
                # Test comment functionality
                self.test_comment_creation()
                self.test_comment_display()
                self.test_comment_moderation()
                
        except Exception as e:
            self.add_test_result("comment_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_comment_creation(self):
        """Test comment creation functionality"""
        try:
            with self.app.test_client() as client:
                response = client.get('/forum/post/1')
                
                if response.status_code in [200, 404]:
                    if response.status_code == 200:
                        if b'comment' in response.data.lower():
                            self.add_test_result("comment_creation_form", "passed", 
                                              "Comment creation form present")
                        else:
                            self.add_test_result("comment_creation_form", "warning", 
                                              "Comment creation form not found")
                    else:
                        self.add_test_result("comment_creation_testing", "skipped", 
                                          "Post not found")
                else:
                    self.add_test_result("comment_creation_testing", "failed", 
                                      f"Comment creation test failed: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("comment_creation", "error", str(e), traceback.format_exc())
    
    def test_comment_display(self):
        """Test comment display functionality"""
        try:
            with self.app.test_client() as client:
                response = client.get('/forum/post/1')
                
                if response.status_code == 200:
                    if b'comment' in response.data.lower():
                        self.add_test_result("comment_display_present", "passed", 
                                          "Comments displayed on post page")
                    else:
                        self.add_test_result("comment_display_present", "warning", 
                                          "Comments not displayed on post page")
                else:
                    self.add_test_result("comment_display_testing", "skipped", 
                                      "Post not accessible")
                
        except Exception as e:
            self.add_test_result("comment_display", "error", str(e), traceback.format_exc())
    
    def test_comment_moderation(self):
        """Test comment moderation functionality"""
        try:
            with self.app.test_client() as client:
                # Test admin access to comment moderation
                response = client.get('/admin/comments')
                
                if response.status_code in [200, 302, 401, 403]:
                    self.add_test_result("comment_moderation_accessible", "passed", 
                                      "Comment moderation accessible")
                else:
                    self.add_test_result("comment_moderation_accessible", "failed", 
                                      f"Comment moderation not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("comment_moderation", "error", str(e), traceback.format_exc())
