"""
Comprehensive Admin Forms Tests for Repo-Forum Project
Tests admin form functionality.
"""

import re
import traceback
from datetime import datetime

class AdminFormsTest:
    """Comprehensive admin forms testing for entire app"""
    
    def __init__(self, framework):
        self.framework = framework
        self.app = None
        self.test_results = []
    
    def add_test_result(self, test_name, status, message, details=None):
        """Add test result to framework"""
        self.framework.test_results.append({
            "test_name": test_name,
            "category": "admin",
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def run_all_tests(self):
        """Run all admin forms tests"""
        print("📝 Running Comprehensive Admin Forms Tests...")
        
        try:
            # Initialize Flask app
            from app import create_app
            self.app = create_app()
            
            with self.app.app_context():
                # Test admin form functionality
                self.test_user_management_forms()
                self.test_post_management_forms()
                self.test_category_management_forms()
                
        except Exception as e:
            self.add_test_result("admin_forms_test_initialization", "error", str(e), traceback.format_exc())
        
        return self.test_results
    
    def test_user_management_forms(self):
        """Test user management forms"""
        try:
            with self.app.test_client() as client:
                response = client.get('/admin/users')
                
                if response.status_code in [200, 302]:
                    self.add_test_result("user_management_form_accessible", "passed", 
                                      "User management form accessible")
                else:
                    self.add_test_result("user_management_form_accessible", "failed", 
                                      f"User management form not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("user_management_forms", "error", str(e), traceback.format_exc())
    
    def test_post_management_forms(self):
        """Test post management forms"""
        try:
            with self.app.test_client() as client:
                response = client.get('/admin/posts')
                
                if response.status_code in [200, 302]:
                    self.add_test_result("post_management_form_accessible", "passed", 
                                      "Post management form accessible")
                else:
                    self.add_test_result("post_management_form_accessible", "failed", 
                                      f"Post management form not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("post_management_forms", "error", str(e), traceback.format_exc())
    
    def test_category_management_forms(self):
        """Test category management forms"""
        try:
            with self.app.test_client() as client:
                response = client.get('/admin/categories')
                
                if response.status_code in [200, 302]:
                    self.add_test_result("category_management_form_accessible", "passed", 
                                      "Category management form accessible")
                else:
                    self.add_test_result("category_management_form_accessible", "failed", 
                                      f"Category management form not accessible: {response.status_code}")
                
        except Exception as e:
            self.add_test_result("category_management_forms", "error", str(e), traceback.format_exc())
